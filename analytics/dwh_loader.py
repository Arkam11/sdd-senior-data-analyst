"""
SDD Government Services - DWH Loader
Reads from Oracle OLTP and loads the Star Schema DWH tables
"""

import oracledb

DB_HOST    = "localhost"
DB_PORT    = 1521
DB_SERVICE = "FREEPDB1"
DB_USER    = "sdd_user"
DB_PASS    = "SDD_User_2024"


def get_connection():
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    )


def load_dim_department(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dim_department")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  dim_department already loaded, skipping")
        cursor.close()
        return
    cursor.execute("""
        INSERT INTO dim_department (department_id, department_code, department_name, department_sector)
        SELECT department_id, department_code, department_name, department_sector
        FROM departments
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM dim_department")
    print(f"  ✅ dim_department loaded: {cursor.fetchone()[0]} rows")
    cursor.close()


def load_dim_service_type(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dim_service_type")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  dim_service_type already loaded, skipping")
        cursor.close()
        return
    cursor.execute("""
        INSERT INTO dim_service_type (service_type_id, service_code, service_name, category)
        SELECT service_type_id, service_code, service_name, category
        FROM service_types
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM dim_service_type")
    print(f"  ✅ dim_service_type loaded: {cursor.fetchone()[0]} rows")
    cursor.close()


def load_dim_sla(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dim_sla")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  dim_sla already loaded, skipping")
        cursor.close()
        return
    cursor.execute("""
        INSERT INTO dim_sla (sla_id, priority_level, sla_hours, sla_category)
        SELECT
            s.sla_id,
            s.priority_level,
            s.sla_hours,
            CASE
                WHEN s.sla_hours <= 24  THEN 'Same Day'
                WHEN s.sla_hours <= 72  THEN 'Standard'
                WHEN s.sla_hours <= 168 THEN 'Extended'
                ELSE 'Long Term'
            END AS sla_category
        FROM sla_definitions s
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM dim_sla")
    print(f"  ✅ dim_sla loaded: {cursor.fetchone()[0]} rows")
    cursor.close()


def load_fact_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_service_requests")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  fact_service_requests already loaded, skipping")
        cursor.close()
        return

    cursor.execute("""
        INSERT INTO fact_service_requests (
            request_id, request_ref,
            dept_key, service_key, time_key, sla_key,
            channel, status, priority,
            resolution_minutes, sla_hours_allowed,
            sla_compliant_flag, sla_breach_minutes,
            satisfaction_score, ease_of_use_score, response_speed_score,
            has_survey, submitted_at, completed_at
        )
        SELECT
            sr.request_id,
            sr.request_ref,
            dd.dept_key,
            ds.service_key,
            TO_NUMBER(TO_CHAR(sr.submitted_at, 'YYYYMMDD')) AS time_key,
            dl.sla_key,
            sr.channel,
            sr.status,
            sr.priority,
            sr.resolution_minutes,
            sla.sla_hours,
            sr.sla_compliant,
            CASE
                WHEN sr.sla_compliant = 0
                THEN sr.resolution_minutes - (sla.sla_hours * 60)
                ELSE 0
            END AS sla_breach_minutes,
            us.satisfaction_score,
            us.ease_of_use_score,
            us.response_speed_score,
            CASE WHEN us.survey_id IS NOT NULL THEN 1 ELSE 0 END AS has_survey,
            sr.submitted_at,
            sr.completed_at
        FROM service_requests sr
        JOIN dim_department   dd  ON sr.department_id   = dd.department_id
        JOIN dim_service_type ds  ON sr.service_type_id = ds.service_type_id
        JOIN dim_sla          dl  ON sr.sla_id          = dl.sla_id
        JOIN sla_definitions  sla ON sr.sla_id          = sla.sla_id
        LEFT JOIN user_surveys us ON sr.request_id      = us.request_id
    """)
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM fact_service_requests")
    print(f"  ✅ fact_service_requests loaded: {cursor.fetchone()[0]} rows")
    cursor.close()


def verify_kpis(conn):
    cursor = conn.cursor()
    print("\n📊 KPI Verification Snapshot:")

    cursor.execute("""
        SELECT ROUND(AVG(resolution_minutes)/60, 2)
        FROM fact_service_requests
    """)
    print(f"  • Overall avg resolution time : {cursor.fetchone()[0]} hours")

    cursor.execute("""
        SELECT ROUND(SUM(sla_compliant_flag) / COUNT(*) * 100, 2)
        FROM fact_service_requests
    """)
    print(f"  • Overall SLA compliance      : {cursor.fetchone()[0]}%")

    cursor.execute("""
        SELECT ROUND(AVG(satisfaction_score), 2)
        FROM fact_service_requests
        WHERE has_survey = 1
    """)
    print(f"  • Overall avg satisfaction    : {cursor.fetchone()[0]} / 5.0")

    cursor.execute("SELECT COUNT(*) FROM fact_service_requests")
    print(f"  • Total fact rows             : {cursor.fetchone()[0]}")
    cursor.close()


def main():
    print("\n🚀 SDD DWH Loader starting...\n")
    conn = get_connection()
    print("✅ Connected to Oracle FREEPDB1\n")

    print("📦 Loading dimension tables...")
    load_dim_department(conn)
    load_dim_service_type(conn)
    load_dim_sla(conn)

    print("\n📋 Loading fact table...")
    load_fact_table(conn)

    verify_kpis(conn)

    conn.close()
    print("\n✅ DWH load complete!")


if __name__ == "__main__":
    main()
