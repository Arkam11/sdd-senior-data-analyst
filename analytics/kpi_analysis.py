"""
SDD Government Services - KPI Analysis & Chart Generator
"""

import os
import oracledb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

DB_HOST    = "localhost"
DB_PORT    = 1521
DB_SERVICE = "FREEPDB1"
DB_USER    = "sdd_user"
DB_PASS    = "SDD_User_2024"

OUTPUT_DIR = "dashboard"
os.makedirs(OUTPUT_DIR, exist_ok=True)

BRAND_COLORS = ["#2563EB", "#16A34A", "#DC2626", "#D97706", "#7C3AED",
                "#0891B2", "#DB2777", "#65A30D"]

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.family":      "sans-serif",
    "font.size":        11,
})


def get_connection():
    return oracledb.connect(
        user=DB_USER, password=DB_PASS,
        dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    )


def fetch(conn, sql):
    cursor = conn.cursor()
    cursor.execute(sql)
    cols = [d[0].lower() for d in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return pd.DataFrame(rows, columns=cols)


def chart_requests_per_dept(conn):
    df = fetch(conn, """
        SELECT d.department_name, COUNT(f.fact_id) AS total_requests
        FROM fact_service_requests f
        JOIN dim_department d ON f.dept_key = d.dept_key
        GROUP BY d.department_name
        ORDER BY total_requests DESC
    """)
    df["department_name"] = df["department_name"].str.replace("Ministry of ", "", regex=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(df["department_name"], df["total_requests"],
                   color=BRAND_COLORS[:len(df)], edgecolor="white", height=0.6)
    for bar, val in zip(bars, df["total_requests"]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                str(int(val)), va="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("Number of Requests")
    ax.set_title("Service Requests per Department", fontsize=14, fontweight="bold", pad=15)
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart1_requests_per_dept.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")
    return df


def chart_sla_trend(conn):
    df = fetch(conn, """
        SELECT t.year_num, t.month_num, t.month_name,
               ROUND(SUM(f.sla_compliant_flag) / COUNT(f.fact_id) * 100, 1) AS sla_pct
        FROM fact_service_requests f
        JOIN dim_time t ON f.time_key = t.time_key
        GROUP BY t.year_num, t.month_num, t.month_name
        ORDER BY t.year_num, t.month_num
    """)
    df["period"] = df["month_name"].str[:3] + " " + df["year_num"].astype(str)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["period"], df["sla_pct"], marker="o", linewidth=2.5,
            color="#2563EB", markersize=6, markerfacecolor="white", markeredgewidth=2)
    ax.axhline(y=80, color="#DC2626", linestyle="--", linewidth=1.5,
               alpha=0.7, label="80% Target")
    ax.fill_between(range(len(df)), df["sla_pct"], alpha=0.08, color="#2563EB")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(60, 100)
    ax.set_xlabel("Month")
    ax.set_ylabel("SLA Compliance %")
    ax.set_title("SLA Compliance Trend (2024-2025)", fontsize=14, fontweight="bold", pad=15)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart2_sla_trend.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")
    return df


def chart_satisfaction_vs_sla(conn):
    df = fetch(conn, """
        SELECT
            d.department_name,
            ROUND(AVG(f.satisfaction_score), 2) AS avg_satisfaction,
            ROUND(SUM(f.sla_compliant_flag) / COUNT(f.fact_id) * 100, 1) AS sla_pct,
            COUNT(f.fact_id) AS total_requests
        FROM fact_service_requests f
        JOIN dim_department d ON f.dept_key = d.dept_key
        WHERE f.has_survey = 1
        GROUP BY d.department_name
    """)
    df["department_name"] = df["department_name"].str.replace("Ministry of ", "", regex=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(
        df["sla_pct"], df["avg_satisfaction"],
        s=df["total_requests"] * 0.4,
        c=BRAND_COLORS[:len(df)], alpha=0.85, edgecolors="white", linewidth=1.5
    )
    for _, row in df.iterrows():
        ax.annotate(row["department_name"],
                    (row["sla_pct"], row["avg_satisfaction"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=9)
    ax.axvline(x=75, color="#DC2626", linestyle="--", alpha=0.5, label="75% SLA target")
    ax.axhline(y=3.5, color="#D97706", linestyle="--", alpha=0.5, label="3.5 satisfaction target")
    ax.set_xlabel("SLA Compliance %")
    ax.set_ylabel("Avg Satisfaction Score (1-5)")
    ax.set_title("Satisfaction Score vs SLA Compliance\n(bubble size = request volume)",
                 fontsize=13, fontweight="bold", pad=15)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart3_satisfaction_vs_sla.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")
    return df


def chart_resolution_time(conn):
    df = fetch(conn, """
        SELECT
            d.department_name,
            ROUND(AVG(f.resolution_minutes) / 60, 1) AS avg_hours,
            ROUND(AVG(f.sla_hours_allowed), 1) AS sla_hours
        FROM fact_service_requests f
        JOIN dim_department d ON f.dept_key = d.dept_key
        GROUP BY d.department_name
        ORDER BY avg_hours DESC
    """)
    df["department_name"] = df["department_name"].str.replace("Ministry of ", "", regex=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(df))
    ax.bar(x, df["avg_hours"], color="#2563EB", alpha=0.85,
           label="Avg Resolution (hrs)", width=0.4)
    ax.bar([i + 0.4 for i in x], df["sla_hours"], color="#16A34A", alpha=0.6,
           label="SLA Allowance (hrs)", width=0.4)
    ax.set_xticks([i + 0.2 for i in x])
    ax.set_xticklabels(df["department_name"], rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("Hours")
    ax.set_title("Avg Resolution Time vs SLA Allowance per Department",
                 fontsize=13, fontweight="bold", pad=15)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart4_resolution_time.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")
    return df


def chart_kpi_tiles(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*),
            ROUND(SUM(sla_compliant_flag) / COUNT(*) * 100, 1),
            ROUND(AVG(CASE WHEN has_survey=1 THEN satisfaction_score END), 2),
            ROUND(AVG(resolution_minutes) / 60, 1)
        FROM fact_service_requests
    """)
    total, sla_pct, sat, res = cursor.fetchone()
    cursor.close()

    kpis = [
        ("Total Requests",      f"{int(total):,}", "#2563EB"),
        ("SLA Compliance",      f"{sla_pct}%",     "#16A34A"),
        ("Avg Satisfaction",    f"{sat} / 5.0",    "#7C3AED"),
        ("Avg Resolution Time", f"{res} hrs",      "#D97706"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(14, 3))
    for ax, (label, value, color) in zip(axes, kpis):
        ax.set_facecolor(color)
        ax.text(0.5, 0.6, value, ha="center", va="center",
                fontsize=22, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.text(0.5, 0.25, label, ha="center", va="center",
                fontsize=11, color="white", alpha=0.9,
                transform=ax.transAxes)
        ax.axis("off")
    fig.suptitle("Executive KPI Dashboard - SDD Government Services",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = f"{OUTPUT_DIR}/chart5_kpi_tiles.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {path}")


def main():
    print("SDD KPI Analysis starting...")
    conn = get_connection()
    print("Connected to Oracle DWH\n")

    print("Generating charts...")
    chart_requests_per_dept(conn)
    chart_sla_trend(conn)
    chart_satisfaction_vs_sla(conn)
    chart_resolution_time(conn)
    chart_kpi_tiles(conn)

    conn.close()
    print(f"\nAll charts saved to ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
