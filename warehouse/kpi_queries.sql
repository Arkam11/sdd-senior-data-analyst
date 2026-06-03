-- ============================================================
-- SDD Government Services - KPI Queries
-- Run against Oracle DWH (sdd_user @ FREEPDB1)
-- ============================================================

-- ------------------------------------------------------------
-- KPI 1: Average Resolution Time per Department (in hours)
-- ------------------------------------------------------------
SELECT
    d.department_name,
    d.department_sector,
    COUNT(f.fact_id)                                    AS total_requests,
    ROUND(AVG(f.resolution_minutes) / 60, 2)           AS avg_resolution_hours,
    ROUND(MIN(f.resolution_minutes) / 60, 2)           AS min_resolution_hours,
    ROUND(MAX(f.resolution_minutes) / 60, 2)           AS max_resolution_hours
FROM
    fact_service_requests f
    JOIN dim_department d ON f.dept_key = d.dept_key
WHERE
    f.resolution_minutes IS NOT NULL
GROUP BY
    d.department_name,
    d.department_sector
ORDER BY
    avg_resolution_hours ASC;


-- ------------------------------------------------------------
-- KPI 2: SLA Compliance % per Service Type per Month
-- ------------------------------------------------------------
SELECT
    t.year_num,
    t.month_name,
    t.month_num,
    s.service_name,
    s.category,
    COUNT(f.fact_id)                                        AS total_requests,
    SUM(f.sla_compliant_flag)                               AS compliant_count,
    ROUND(SUM(f.sla_compliant_flag) / COUNT(f.fact_id) * 100, 2) AS sla_compliance_pct
FROM
    fact_service_requests f
    JOIN dim_time         t ON f.time_key    = t.time_key
    JOIN dim_service_type s ON f.service_key = s.service_key
GROUP BY
    t.year_num,
    t.month_name,
    t.month_num,
    s.service_name,
    s.category
ORDER BY
    t.year_num,
    t.month_num,
    sla_compliance_pct DESC;


-- ------------------------------------------------------------
-- KPI 3: Satisfaction Score vs SLA Compliance Correlation
-- ------------------------------------------------------------
SELECT
    d.department_name,
    s.service_name,
    COUNT(f.fact_id)                                             AS total_requests,
    SUM(f.has_survey)                                            AS survey_count,
    ROUND(AVG(f.satisfaction_score), 2)                         AS avg_satisfaction,
    ROUND(AVG(f.ease_of_use_score), 2)                          AS avg_ease_of_use,
    ROUND(AVG(f.response_speed_score), 2)                       AS avg_response_speed,
    ROUND(SUM(f.sla_compliant_flag) / COUNT(f.fact_id) * 100, 2) AS sla_compliance_pct,
    CASE
        WHEN AVG(f.satisfaction_score) >= 4.0 THEN 'High Satisfaction'
        WHEN AVG(f.satisfaction_score) >= 3.0 THEN 'Medium Satisfaction'
        ELSE 'Low Satisfaction'
    END AS satisfaction_band
FROM
    fact_service_requests f
    JOIN dim_department   d ON f.dept_key    = d.dept_key
    JOIN dim_service_type s ON f.service_key = s.service_key
WHERE
    f.has_survey = 1
GROUP BY
    d.department_name,
    s.service_name
ORDER BY
    avg_satisfaction DESC;


-- ------------------------------------------------------------
-- BONUS KPI 4: Monthly Request Volume Trend
-- ------------------------------------------------------------
SELECT
    t.year_num,
    t.month_name,
    t.month_num,
    t.quarter_name,
    COUNT(f.fact_id)                                             AS total_requests,
    ROUND(SUM(f.sla_compliant_flag) / COUNT(f.fact_id) * 100, 2) AS sla_compliance_pct,
    ROUND(AVG(f.satisfaction_score), 2)                          AS avg_satisfaction,
    ROUND(AVG(f.resolution_minutes) / 60, 2)                    AS avg_resolution_hours
FROM
    fact_service_requests f
    JOIN dim_time t ON f.time_key = t.time_key
GROUP BY
    t.year_num,
    t.month_name,
    t.month_num,
    t.quarter_name
ORDER BY
    t.year_num,
    t.month_num;


-- ------------------------------------------------------------
-- BONUS KPI 5: Top 5 Departments by SLA Breach Count
-- ------------------------------------------------------------
SELECT
    d.department_name,
    COUNT(f.fact_id)                        AS total_requests,
    SUM(CASE WHEN f.sla_compliant_flag = 0 THEN 1 ELSE 0 END) AS breach_count,
    ROUND(
        SUM(CASE WHEN f.sla_compliant_flag = 0 THEN 1 ELSE 0 END)
        / COUNT(f.fact_id) * 100, 2
    )                                       AS breach_pct,
    ROUND(AVG(f.resolution_minutes) / 60, 2) AS avg_resolution_hours
FROM
    fact_service_requests f
    JOIN dim_department d ON f.dept_key = d.dept_key
GROUP BY
    d.department_name
ORDER BY
    breach_count DESC
FETCH FIRST 5 ROWS ONLY;

