-- ============================================================
-- SDD Government Services - OLTP Schema
-- Oracle Free 23c
-- ============================================================

-- Connect as sdd_user to FREEPDB1

-- ------------------------------------------------------------
-- 1. DEPARTMENTS
-- ------------------------------------------------------------
CREATE TABLE departments (
    department_id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_code   VARCHAR2(10)  NOT NULL UNIQUE,
    department_name   VARCHAR2(100) NOT NULL,
    department_sector VARCHAR2(50),
    created_at        DATE DEFAULT SYSDATE
);

-- ------------------------------------------------------------
-- 2. SERVICE TYPES
-- ------------------------------------------------------------
CREATE TABLE service_types (
    service_type_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_code      VARCHAR2(20)  NOT NULL UNIQUE,
    service_name      VARCHAR2(100) NOT NULL,
    department_id     NUMBER        NOT NULL,
    category          VARCHAR2(50),
    created_at        DATE DEFAULT SYSDATE,
    CONSTRAINT fk_st_dept FOREIGN KEY (department_id)
        REFERENCES departments(department_id)
);

-- ------------------------------------------------------------
-- 3. SLA DEFINITIONS
-- ------------------------------------------------------------
CREATE TABLE sla_definitions (
    sla_id            NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_type_id   NUMBER       NOT NULL,
    priority_level    VARCHAR2(20) NOT NULL,
    sla_hours         NUMBER(5,2)  NOT NULL,
    created_at        DATE DEFAULT SYSDATE,
    CONSTRAINT fk_sla_st FOREIGN KEY (service_type_id)
        REFERENCES service_types(service_type_id)
);

-- ------------------------------------------------------------
-- 4. SERVICE REQUESTS
-- ------------------------------------------------------------
CREATE TABLE service_requests (
    request_id        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_ref       VARCHAR2(20)  NOT NULL UNIQUE,
    department_id     NUMBER        NOT NULL,
    service_type_id   NUMBER        NOT NULL,
    sla_id            NUMBER        NOT NULL,
    requester_name    VARCHAR2(100),
    requester_email   VARCHAR2(150),
    channel           VARCHAR2(20),
    status            VARCHAR2(20)  DEFAULT 'SUBMITTED',
    priority          VARCHAR2(20)  DEFAULT 'NORMAL',
    submitted_at      TIMESTAMP     NOT NULL,
    assigned_at       TIMESTAMP,
    completed_at      TIMESTAMP,
    resolution_minutes NUMBER(10,2),
    sla_deadline      TIMESTAMP,
    sla_compliant     NUMBER(1)     DEFAULT 0,
    notes             VARCHAR2(500),
    created_at        DATE DEFAULT SYSDATE,
    CONSTRAINT fk_sr_dept FOREIGN KEY (department_id)
        REFERENCES departments(department_id),
    CONSTRAINT fk_sr_st FOREIGN KEY (service_type_id)
        REFERENCES service_types(service_type_id),
    CONSTRAINT fk_sr_sla FOREIGN KEY (sla_id)
        REFERENCES sla_definitions(sla_id)
);

-- ------------------------------------------------------------
-- 5. USER SURVEYS
-- ------------------------------------------------------------
CREATE TABLE user_surveys (
    survey_id         NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id        NUMBER        NOT NULL UNIQUE,
    satisfaction_score NUMBER(2,1)  NOT NULL,
    ease_of_use_score  NUMBER(2,1),
    response_speed_score NUMBER(2,1),
    comments          VARCHAR2(500),
    surveyed_at       TIMESTAMP DEFAULT SYSTIMESTAMP,
    CONSTRAINT fk_surv_req FOREIGN KEY (request_id)
        REFERENCES service_requests(request_id),
    CONSTRAINT chk_score CHECK (satisfaction_score BETWEEN 1 AND 5)
);

-- ------------------------------------------------------------
-- INDEXES for ETL performance
-- ------------------------------------------------------------
CREATE INDEX idx_sr_dept     ON service_requests(department_id);
CREATE INDEX idx_sr_st       ON service_requests(service_type_id);
CREATE INDEX idx_sr_status   ON service_requests(status);
CREATE INDEX idx_sr_submitted ON service_requests(submitted_at);
CREATE INDEX idx_sr_sla      ON service_requests(sla_compliant);

