"""
SDD Government Services - Architecture Diagram Generator
Produces a professional PDF architecture diagram
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np
import os

OUTPUT_DIR = "diagrams"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Colors ───────────────────────────────────────────────────
C = {
    "oracle":   "#C74634",
    "nifi":     "#728E9B",
    "kafka":    "#231F20",
    "spark":    "#E25A1C",
    "dwh":      "#1A5276",
    "tableau":  "#4E79A7",
    "python":   "#3776AB",
    "aws":      "#FF9900",
    "bg":       "#F8F9FA",
    "arrow":    "#555555",
    "white":    "#FFFFFF",
    "text_dark":"#1A1A2E",
    "border":   "#CCCCCC",
}


def rounded_box(ax, x, y, w, h, color, label, sublabel=None, fontsize=9):
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.02",
        facecolor=color, edgecolor=C["white"],
        linewidth=1.5, zorder=3
    )
    ax.add_patch(box)
    if sublabel:
        ax.text(x, y + 0.08, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=C["white"], zorder=4)
        ax.text(x, y - 0.1, sublabel, ha="center", va="center",
                fontsize=7, color=C["white"], alpha=0.85, zorder=4)
    else:
        ax.text(x, y, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=C["white"], zorder=4)


def arrow(ax, x1, y1, x2, y2, label=None, color=None):
    c = color or C["arrow"]
    ax.annotate("",
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=c,
            lw=1.8,
            connectionstyle="arc3,rad=0.0"
        ), zorder=2
    )
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.07, label, ha="center", va="bottom",
                fontsize=7, color=c, style="italic", zorder=5)


def section_box(ax, x, y, w, h, label, color, alpha=0.08):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.03",
        facecolor=color, edgecolor=color,
        linewidth=1.5, alpha=alpha, zorder=1
    )
    ax.add_patch(box)
    ax.text(x + 0.08, y + h - 0.1, label,
            fontsize=8, fontweight="bold", color=color,
            alpha=0.9, zorder=2, va="top")


def main():
    fig, ax = plt.subplots(figsize=(18, 11))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 11)
    ax.axis("off")
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    # ── Title ─────────────────────────────────────────────────
    ax.text(9, 10.5, "SDD Government Services — Enterprise Data Analytics Architecture",
            ha="center", va="center", fontsize=14, fontweight="bold",
            color=C["text_dark"])
    ax.text(9, 10.15, "Oracle OLTP  →  Apache NiFi  →  Kafka  →  Spark  →  Oracle DWH  →  Tableau",
            ha="center", va="center", fontsize=9, color="#555555", style="italic")

    # ── Section backgrounds ───────────────────────────────────
    section_box(ax, 0.2,  1.5, 2.8, 7.5, "Source Layer",       C["oracle"])
    section_box(ax, 3.2,  1.5, 2.8, 7.5, "Ingestion Layer",    C["nifi"])
    section_box(ax, 6.2,  1.5, 2.8, 7.5, "Streaming Layer",    C["kafka"])
    section_box(ax, 9.2,  1.5, 2.8, 7.5, "Transform Layer",    C["spark"])
    section_box(ax, 12.2, 1.5, 2.8, 7.5, "Storage Layer",      C["dwh"])
    section_box(ax, 15.2, 1.5, 2.5, 7.5, "Presentation Layer", C["tableau"])

    # ── Source Layer ──────────────────────────────────────────
    rounded_box(ax, 1.6, 8.3, 2.0, 0.55, C["oracle"],
                "Oracle OLTP", "23c Free (FREEPDB1)")
    rounded_box(ax, 1.6, 7.2, 2.0, 0.55, C["oracle"],
                "SERVICE_REQUESTS", "1,200 rows")
    rounded_box(ax, 1.6, 6.1, 2.0, 0.55, C["oracle"],
                "USER_SURVEYS", "846 rows")
    rounded_box(ax, 1.6, 5.0, 2.0, 0.55, C["oracle"],
                "DEPARTMENTS", "8 rows")
    rounded_box(ax, 1.6, 3.9, 2.0, 0.55, C["oracle"],
                "SERVICE_TYPES", "16 rows")
    rounded_box(ax, 1.6, 2.8, 2.0, 0.55, C["oracle"],
                "SLA_DEFINITIONS", "16 rows")

    # ── Ingestion Layer (NiFi) ────────────────────────────────
    rounded_box(ax, 4.6, 8.3, 2.2, 0.55, C["nifi"],
                "Apache NiFi", "v1.23.2")
    rounded_box(ax, 4.6, 7.2, 2.2, 0.55, C["nifi"],
                "QueryDatabaseTable", "Extract from OLTP")
    rounded_box(ax, 4.6, 6.1, 2.2, 0.55, C["nifi"],
                "EvaluateJsonPath", "Parse & validate")
    rounded_box(ax, 4.6, 5.0, 2.2, 0.55, C["nifi"],
                "UpdateAttribute", "SLA flag calculation")
    rounded_box(ax, 4.6, 3.9, 2.2, 0.55, C["nifi"],
                "ConvertRecord", "Transform schema")
    rounded_box(ax, 4.6, 2.8, 2.2, 0.55, C["nifi"],
                "PutDatabaseRecord", "Load to DWH")

    # ── Streaming Layer (Kafka) ───────────────────────────────
    rounded_box(ax, 7.6, 8.3, 2.2, 0.55, C["kafka"],
                "Apache Kafka", "v7.5.0")
    rounded_box(ax, 7.6, 7.2, 2.2, 0.55, C["kafka"],
                "Kafka Producer", "Real-time events")
    rounded_box(ax, 7.6, 6.1, 2.2, 0.55, C["kafka"],
                "Topic:", "sdd-service-requests")
    rounded_box(ax, 7.6, 5.0, 2.2, 0.55, C["kafka"],
                "Zookeeper", "Cluster coordinator")
    rounded_box(ax, 7.6, 3.9, 2.2, 0.55, C["kafka"],
                "Kafka Consumer", "Event processing")
    rounded_box(ax, 7.6, 2.8, 2.2, 0.55, C["python"],
                "kafka_producer.py", "20 events streamed")

    # ── Transform Layer (Spark) ───────────────────────────────
    rounded_box(ax, 10.6, 8.3, 2.2, 0.55, C["spark"],
                "Apache Spark", "PySpark 3.5")
    rounded_box(ax, 10.6, 7.2, 2.2, 0.55, C["spark"],
                "DataFrame API", "Spark-style transforms")
    rounded_box(ax, 10.6, 6.1, 2.2, 0.55, C["spark"],
                "KPI 1", "Avg Resolution Time")
    rounded_box(ax, 10.6, 5.0, 2.2, 0.55, C["spark"],
                "KPI 2", "SLA Compliance %")
    rounded_box(ax, 10.6, 3.9, 2.2, 0.55, C["spark"],
                "KPI 3", "Satisfaction Score")
    rounded_box(ax, 10.6, 2.8, 2.2, 0.55, C["python"],
                "spark_transform.py", "4 KPI CSVs output")

    # ── Storage Layer (DWH) ───────────────────────────────────
    rounded_box(ax, 13.6, 8.3, 2.2, 0.55, C["dwh"],
                "Oracle DWH", "Star Schema")
    rounded_box(ax, 13.6, 7.2, 2.2, 0.55, C["dwh"],
                "FACT_SERVICE_REQUESTS", "1,200 rows")
    rounded_box(ax, 13.6, 6.1, 2.2, 0.55, C["dwh"],
                "DIM_DEPARTMENT", "8 rows")
    rounded_box(ax, 13.6, 5.0, 2.2, 0.55, C["dwh"],
                "DIM_SERVICE_TYPE", "16 rows")
    rounded_box(ax, 13.6, 3.9, 2.2, 0.55, C["dwh"],
                "DIM_TIME", "731 rows")
    rounded_box(ax, 13.6, 2.8, 2.2, 0.55, C["dwh"],
                "DIM_SLA", "16 rows")

    # ── Presentation Layer (Tableau) ──────────────────────────
    rounded_box(ax, 16.4, 8.3, 2.0, 0.55, C["tableau"],
                "Tableau Desktop", "Executive Dashboard")
    rounded_box(ax, 16.4, 7.2, 2.0, 0.55, C["tableau"],
                "Requests by Dept", "Bar chart")
    rounded_box(ax, 16.4, 6.1, 2.0, 0.55, C["tableau"],
                "SLA Trend", "Line chart")
    rounded_box(ax, 16.4, 5.0, 2.0, 0.55, C["tableau"],
                "Satisfaction vs SLA", "Scatter plot")
    rounded_box(ax, 16.4, 3.9, 2.0, 0.55, C["tableau"],
                "KPI Tiles", "Summary metrics")
    rounded_box(ax, 16.4, 2.8, 2.0, 0.55, C["python"],
                "kpi_analysis.py", "5 charts exported")

    # ── Main flow arrows ──────────────────────────────────────
    for y in [8.3, 7.2, 6.1, 5.0, 3.9, 2.8]:
        arrow(ax, 2.61, y, 3.49, y)
        arrow(ax, 5.71, y, 6.49, y)
        arrow(ax, 8.71, y, 9.49, y)
        arrow(ax, 11.71, y, 12.49, y)
        arrow(ax, 14.71, y, 15.39, y)

    # ── CI/CD footer ──────────────────────────────────────────
    section_box(ax, 0.2, 0.2, 17.5, 1.1, "", "#2D6A4F", alpha=0.06)
    rounded_box(ax, 2.5,  0.75, 2.8, 0.55, "#2D6A4F",
                "GitHub Actions CI/CD", "Lint + Test on push")
    rounded_box(ax, 6.0,  0.75, 2.8, 0.55, "#2D6A4F",
                "Docker Compose", "Full stack orchestration")
    rounded_box(ax, 9.5,  0.75, 2.8, 0.55, "#2D6A4F",
                "GitHub Repository", "github.com/Arkam11")
    rounded_box(ax, 13.0, 0.75, 2.8, 0.55, "#2D6A4F",
                "WSL2 / Ubuntu", "Windows 10 host")
    ax.text(0.4, 1.15, "DevOps Layer",
            fontsize=8, fontweight="bold", color="#2D6A4F", alpha=0.9)

    # ── Legend ────────────────────────────────────────────────
    legend_items = [
        mpatches.Patch(color=C["oracle"],  label="Oracle DB"),
        mpatches.Patch(color=C["nifi"],    label="Apache NiFi"),
        mpatches.Patch(color=C["kafka"],   label="Kafka/Zookeeper"),
        mpatches.Patch(color=C["spark"],   label="Apache Spark"),
        mpatches.Patch(color=C["dwh"],     label="Data Warehouse"),
        mpatches.Patch(color=C["tableau"], label="Tableau"),
        mpatches.Patch(color=C["python"],  label="Python Scripts"),
        mpatches.Patch(color="#2D6A4F",    label="DevOps"),
    ]
    ax.legend(handles=legend_items, loc="upper left",
              bbox_to_anchor=(0.0, 0.13), ncol=8,
              fontsize=8, framealpha=0.9,
              fancybox=True, edgecolor=C["border"])

    plt.tight_layout(pad=0.5)
    out_png = f"{OUTPUT_DIR}/architecture_diagram.png"
    out_pdf = f"{OUTPUT_DIR}/architecture_diagram.pdf"
    plt.savefig(out_png, dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.savefig(out_pdf, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Saved {out_png}")
    print(f"Saved {out_pdf}")
    print("Architecture diagram complete!")


if __name__ == "__main__":
    main()
