-- ============================================================
-- SDD Government Services - Data Warehouse Schema
-- Star Schema Design
-- Oracle Free 23c
-- ============================================================

-- ------------------------------------------------------------
-- DIMENSION: DIM_DEPARTMENT
-- ------------------------------------------------------------
CREATE TABLE dim_department (
    dept_key          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id     NUMBER        NOT NULL,
    department_code   VARCHAR2(10)  NOT NULL,
    department_name   VARCHAR2(100) NOT NULL,
    department_sector VARCHAR2(50),
    effective_date    DATE DEFAULT SYSDATE
);

-- ------------------------------------------------------------
-- DIMENSION: DIM_SERVICE_TYPE
-- ------------------------------------------------------------
CREATE TABLE dim_service_type (
    service_key       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_type_id   NUMBER        NOT NULL,
    service_code      VARCHAR2(20)  NOT NULL,
    service_name      VARCHAR2(100) NOT NULL,
    category          VARCHAR2(50),
    effective_date    DATE DEFAULT SYSDATE
);

-- ------------------------------------------------------------
-- DIMENSION: DIM_TIME
-- ------------------------------------------------------------
CREATE TABLE dim_time (
    time_key          NUMBER PRIMARY KEY,
    full_date         DATE          NOT NULL,
    day_of_week       VARCHAR2(10),
    day_num           NUMBER(2),
    week_num          NUMBER(2),
    month_num         NUMBER(2),
    month_name        VARCHAR2(10),
    quarter_num       NUMBER(1),
    quarter_name      VARCHAR2(6),
    year_num          NUMBER(4),
    is_weekend        NUMBER(1),
    is_holiday        NUMBER(1) DEFAULT 0
);

-- ------------------------------------------------------------
-- DIMENSION: DIM_SLA
-- ------------------------------------------------------------
CREATE TABLE dim_sla (
    sla_key           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sla_id            NUMBER        NOT NULL,
    priority_level    VARCHAR2(20)  NOT NULL,
    sla_hours         NUMBER(5,2)   NOT NULL,
    sla_category      VARCHAR2(20),
    effective_date    DATE DEFAULT SYSDATE
);

-- ------------------------------------------------------------
-- FACT TABLE: FACT_SERVICE_REQUESTS
-- ------------------------------------------------------------
CREATE TABLE fact_service_requests (
    fact_id               NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id            NUMBER        NOT NULL,
    request_ref           VARCHAR2(20)  NOT NULL,
    dept_key              NUMBER        NOT NULL,
    service_key           NUMBER        NOT NULL,
    time_key              NUMBER        NOT NULL,
    sla_key               NUMBER        NOT NULL,
    channel               VARCHAR2(20),
    status                VARCHAR2(20),
    priority              VARCHAR2(20),
    resolution_minutes    NUMBER(10,2),
    sla_hours_allowed     NUMBER(5,2),
    sla_compliant_flag    NUMBER(1),
    sla_breach_minutes    NUMBER(10,2),
    satisfaction_score    NUMBER(2,1),
    ease_of_use_score     NUMBER(2,1),
    response_speed_score  NUMBER(2,1),
    has_survey            NUMBER(1) DEFAULT 0,
    submitted_at          TIMESTAMP,
    completed_at          TIMESTAMP,
    load_timestamp        TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_fact_dept    FOREIGN KEY (dept_key)    REFERENCES dim_department(dept_key),
    CONSTRAINT fk_fact_svc     FOREIGN KEY (service_key) REFERENCES dim_service_type(service_key),
    CONSTRAINT fk_fact_time    FOREIGN KEY (time_key)    REFERENCES dim_time(time_key),
    CONSTRAINT fk_fact_sla     FOREIGN KEY (sla_key)     REFERENCES dim_sla(sla_key)
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------
CREATE INDEX idx_fact_dept    ON fact_service_requests(dept_key);
CREATE INDEX idx_fact_svc     ON fact_service_requests(service_key);
CREATE INDEX idx_fact_time    ON fact_service_requests(time_key);
CREATE INDEX idx_fact_sla     ON fact_service_requests(sla_key);
CREATE INDEX idx_fact_comp    ON fact_service_requests(sla_compliant_flag);
CREATE INDEX idx_fact_score   ON fact_service_requests(satisfaction_score);

