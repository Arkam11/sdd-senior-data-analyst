"""
SDD Government Services - Spark-style Transformation Layer

Demonstrates PySpark transformation logic using pandas as the execution engine.
In production, replace pandas operations with identical PySpark DataFrame API calls
by swapping: import pandas as pd -> from pyspark.sql import SparkSession, functions as F

All transformation logic, column names, and KPI calculations are identical to
what would run on a real Spark cluster.
"""

import os
import oracledb
import pandas as pd

DB_HOST    = "localhost"
DB_PORT    = 1521
DB_SERVICE = "FREEPDB1"
DB_USER    = "sdd_user"
DB_PASS    = "SDD_User_2024"

OUTPUT_DIR = "dashboard/spark_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_connection():
    return oracledb.connect(
        user=DB_USER, password=DB_PASS,
        dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    )


def read_table(conn, table):
    """Equivalent to: spark.read.jdbc(url, table, properties)"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    cols = [d[0].lower() for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows, columns=cols)


def transform_kpi1_resolution(df_fact, df_dept):
    """
    KPI 1 - Avg resolution time per department
    PySpark equivalent:
        df_fact.join(df_dept, 'dept_key')
               .groupBy('department_name')
               .agg(F.round(F.avg('resolution_minutes') / 60, 2))
    """
    df = df_fact.merge(df_dept, on="dept_key")
    result = (df.groupby(["department_name", "department_sector"])
                .agg(
                    total_requests=("fact_id", "count"),
                    avg_resolution_hours=("resolution_minutes",
                                          lambda x: round(x.mean() / 60, 2)),
                    min_resolution_hours=("resolution_minutes",
                                          lambda x: round(x.min() / 60, 2)),
                    max_resolution_hours=("resolution_minutes",
                                          lambda x: round(x.max() / 60, 2)),
                )
                .reset_index()
                .sort_values("avg_resolution_hours"))
    return result


def transform_kpi2_sla(df_fact, df_time, df_svc):
    """
    KPI 2 - SLA compliance % per service per month
    PySpark equivalent:
        df_fact.join(df_time, 'time_key').join(df_svc, 'service_key')
               .groupBy('year_num', 'month_num', 'service_name')
               .agg(F.round(F.sum('sla_compliant_flag') /
                            F.count('fact_id') * 100, 2))
    """
    df = df_fact.merge(df_time, on="time_key").merge(df_svc, on="service_key")
    result = (df.groupby(["year_num", "month_num", "month_name", "service_name"])
                .agg(
                    total_requests=("fact_id", "count"),
                    compliant_count=("sla_compliant_flag", "sum"),
                )
                .reset_index())
    result["sla_compliance_pct"] = (
        result["compliant_count"] / result["total_requests"] * 100
    ).round(2)
    return result.sort_values(["year_num", "month_num"])


def transform_kpi3_satisfaction(df_fact, df_dept, df_svc):
    """
    KPI 3 - Satisfaction score vs SLA compliance
    PySpark equivalent:
        df_fact.filter(F.col('has_survey') == 1)
               .join(df_dept, 'dept_key').join(df_svc, 'service_key')
               .groupBy('department_name', 'service_name')
               .agg(F.round(F.avg('satisfaction_score'), 2))
               .withColumn('band', F.when(...))
    """
    df = (df_fact[df_fact["has_survey"] == 1]
          .merge(df_dept, on="dept_key")
          .merge(df_svc, on="service_key"))
    result = (df.groupby(["department_name", "service_name"])
                .agg(
                    total_requests=("fact_id", "count"),
                    avg_satisfaction=("satisfaction_score",
                                      lambda x: round(x.mean(), 2)),
                    avg_ease_of_use=("ease_of_use_score",
                                     lambda x: round(x.mean(), 2)),
                    avg_response_speed=("response_speed_score",
                                        lambda x: round(x.mean(), 2)),
                    sla_compliance_pct=("sla_compliant_flag",
                                        lambda x: round(x.mean() * 100, 2)),
                )
                .reset_index())
    result["satisfaction_band"] = result["avg_satisfaction"].apply(
        lambda x: "High" if x >= 4.0 else ("Medium" if x >= 3.0 else "Low")
    )
    return result.sort_values("avg_satisfaction", ascending=False)


def transform_monthly_trend(df_fact, df_time):
    """
    Monthly volume and KPI trend
    PySpark equivalent:
        df_fact.join(df_time, 'time_key')
               .groupBy('year_num', 'month_num', 'month_name', 'quarter_name')
               .agg(F.count('fact_id'), F.avg('satisfaction_score'), ...)
    """
    df = df_fact.merge(df_time, on="time_key")
    result = (df.groupby(["year_num", "month_num", "month_name", "quarter_name"])
                .agg(
                    total_requests=("fact_id", "count"),
                    sla_compliance_pct=("sla_compliant_flag",
                                        lambda x: round(x.mean() * 100, 2)),
                    avg_satisfaction=("satisfaction_score",
                                      lambda x: round(x.mean(), 2)),
                    avg_resolution_hours=("resolution_minutes",
                                          lambda x: round(x.mean() / 60, 2)),
                )
                .reset_index()
                .sort_values(["year_num", "month_num"]))
    return result


def print_sample(df, title, rows=4):
    print(f"\n--- {title} ---")
    print(df.head(rows).to_string(index=False))


def main():
    print("SDD Spark-style Transformation starting...")
    print("Engine: pandas (drop-in replacement for PySpark DataFrame API)\n")

    conn = get_connection()
    print("Connected to Oracle DWH\n")

    print("Reading DWH tables...")
    df_fact = read_table(conn, "fact_service_requests")
    df_dept = read_table(conn, "dim_department")
    df_svc  = read_table(conn, "dim_service_type")
    df_time = read_table(conn, "dim_time")
    conn.close()
    print(f"  fact_service_requests : {len(df_fact):,} rows")
    print(f"  dim_department        : {len(df_dept):,} rows")
    print(f"  dim_service_type      : {len(df_svc):,} rows")
    print(f"  dim_time              : {len(df_time):,} rows")

    print("\nRunning transformations...")

    kpi1 = transform_kpi1_resolution(df_fact, df_dept)
    kpi1.to_csv(f"{OUTPUT_DIR}/kpi1_resolution.csv", index=False)
    print(f"  KPI1 resolution    : {len(kpi1)} department rows saved")

    kpi2 = transform_kpi2_sla(df_fact, df_time, df_svc)
    kpi2.to_csv(f"{OUTPUT_DIR}/kpi2_sla_compliance.csv", index=False)
    print(f"  KPI2 sla compliance: {len(kpi2)} rows saved")

    kpi3 = transform_kpi3_satisfaction(df_fact, df_dept, df_svc)
    kpi3.to_csv(f"{OUTPUT_DIR}/kpi3_satisfaction.csv", index=False)
    print(f"  KPI3 satisfaction  : {len(kpi3)} rows saved")

    trend = transform_monthly_trend(df_fact, df_time)
    trend.to_csv(f"{OUTPUT_DIR}/kpi4_monthly_trend.csv", index=False)
    print(f"  Monthly trend      : {len(trend)} rows saved")

    print_sample(kpi1, "KPI1: Avg Resolution Time per Department")
    print_sample(kpi2, "KPI2: SLA Compliance % (first 4 rows)")
    print_sample(kpi3, "KPI3: Satisfaction vs SLA")
    print_sample(trend, "Monthly Trend")

    print(f"\nAll outputs saved to ./{OUTPUT_DIR}/")
    print("Spark transformation complete!")


if __name__ == "__main__":
    main()
