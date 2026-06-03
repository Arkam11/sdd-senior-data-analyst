"""
SDD Government Services - Synthetic Data Generator
Populates Oracle OLTP tables with realistic government service request data
"""

import oracledb
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_US')
random.seed(42)

# ── Connection ──────────────────────────────────────────────
DB_HOST    = "localhost"
DB_PORT    = 1521
DB_SERVICE = "FREEPDB1"
DB_USER    = "sdd_user"
DB_PASS    = "SDD_User_2024"

# ── Reference Data ───────────────────────────────────────────
DEPARTMENTS = [
    ("HLTH", "Ministry of Health",       "Healthcare"),
    ("TRAN", "Ministry of Transport",    "Infrastructure"),
    ("FIN",  "Ministry of Finance",      "Financial"),
    ("EDU",  "Ministry of Education",    "Education"),
    ("HOUS", "Ministry of Housing",      "Urban Development"),
    ("ENV",  "Ministry of Environment",  "Sustainability"),
    ("LAB",  "Ministry of Labour",       "Employment"),
    ("INT",  "Ministry of Interior",     "Security"),
]

SERVICES = [
    ("HLTH_REG",   "Health Card Registration",     "HLTH", "Registration", "NORMAL", 48),
    ("HLTH_APT",   "Medical Appointment Booking",  "HLTH", "Appointment",  "HIGH",   24),
    ("HLTH_CERT",  "Medical Certificate Request",  "HLTH", "Certificate",  "NORMAL", 72),
    ("TRAN_LIC",   "Driving License Renewal",      "TRAN", "Licensing",    "NORMAL", 72),
    ("TRAN_REG",   "Vehicle Registration",         "TRAN", "Registration", "NORMAL", 48),
    ("TRAN_FINE",  "Traffic Fine Dispute",         "TRAN", "Dispute",      "HIGH",   24),
    ("FIN_TAX",    "Tax Filing Assistance",        "FIN",  "Financial",    "HIGH",   24),
    ("FIN_GRANT",  "Business Grant Application",   "FIN",  "Financial",    "LOW",    168),
    ("EDU_ENROL",  "School Enrollment",            "EDU",  "Registration", "NORMAL", 48),
    ("EDU_CERT",   "Academic Certificate Request", "EDU",  "Certificate",  "NORMAL", 96),
    ("HOUS_PERM",  "Building Permit Application",  "HOUS", "Permit",       "LOW",    240),
    ("HOUS_MAINT", "Public Housing Maintenance",   "HOUS", "Maintenance",  "HIGH",   24),
    ("ENV_WASTE",  "Waste Collection Request",     "ENV",  "Service",      "NORMAL", 48),
    ("LAB_COMP",   "Labour Complaint Filing",      "LAB",  "Complaint",    "HIGH",   24),
    ("INT_PASS",   "Passport Application",         "INT",  "Document",     "NORMAL", 120),
    ("INT_VISA",   "Visa Application",             "INT",  "Document",     "HIGH",   72),
]

CHANNELS   = ["Online Portal", "Mobile App", "Walk-in", "Call Center", "Email"]
PRIORITIES = ["NORMAL", "NORMAL", "HIGH", "LOW", "URGENT"]


def get_connection():
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    )


def insert_departments(conn):
    cursor = conn.cursor()
    for code, name, sector in DEPARTMENTS:
        cursor.execute("""
            INSERT INTO departments (department_code, department_name, department_sector)
            VALUES (:1, :2, :3)
        """, [code, name, sector])
    conn.commit()
    cursor.execute("SELECT department_code, department_id FROM departments")
    dept_ids = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"  ✅ Inserted {len(dept_ids)} departments")
    cursor.close()
    return dept_ids


def insert_service_types(conn, dept_ids):
    cursor = conn.cursor()
    for code, name, dept_code, category, priority, sla_h in SERVICES:
        cursor.execute("""
            INSERT INTO service_types (service_code, service_name, department_id, category)
            VALUES (:1, :2, :3, :4)
        """, [code, name, dept_ids[dept_code], category])
    conn.commit()
    cursor.execute("SELECT service_code, service_type_id FROM service_types")
    svc_ids = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"  ✅ Inserted {len(svc_ids)} service types")
    cursor.close()
    return svc_ids


def insert_sla_definitions(conn, svc_ids):
    cursor = conn.cursor()
    for code, name, dept_code, category, priority, sla_h in SERVICES:
        cursor.execute("""
            INSERT INTO sla_definitions (service_type_id, priority_level, sla_hours)
            VALUES (:1, :2, :3)
        """, [svc_ids[code], priority, sla_h])
    conn.commit()
    cursor.execute("SELECT service_type_id, sla_id, sla_hours FROM sla_definitions")
    sla_map = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
    print(f"  ✅ Inserted {len(sla_map)} SLA definitions")
    cursor.close()
    return sla_map


def insert_service_requests(conn, dept_ids, svc_ids, sla_map, count=1200):
    cursor = conn.cursor()
    request_ids = []
    start_date  = datetime(2024, 1, 1)
    end_date    = datetime(2025, 12, 31)

    for i in range(count):
        svc       = random.choice(SERVICES)
        svc_code  = svc[0]
        dept_code = svc[2]
        svc_id    = svc_ids[svc_code]
        dept_id   = dept_ids[dept_code]
        sla_id, sla_hours = sla_map[svc_id]

        submitted    = start_date + timedelta(
            seconds=random.randint(0, int((end_date - start_date).total_seconds()))
        )
        assigned     = submitted + timedelta(hours=random.uniform(0.5, 4))
        compliant    = random.random() < 0.75
        resolution_h = random.uniform(1, sla_hours * 0.9) if compliant \
                       else random.uniform(sla_hours * 1.05, sla_hours * 3)
        completed        = submitted + timedelta(hours=resolution_h)
        resolution_mins  = resolution_h * 60
        sla_deadline     = submitted + timedelta(hours=sla_hours)
        ref              = f"REQ-{str(uuid.uuid4())[:8].upper()}"

        # use OUT bind variable for returning id
        out_id = cursor.var(oracledb.NUMBER)
        cursor.execute("""
            INSERT INTO service_requests (
                request_ref, department_id, service_type_id, sla_id,
                requester_name, requester_email, channel, status, priority,
                submitted_at, assigned_at, completed_at,
                resolution_minutes, sla_deadline, sla_compliant
            ) VALUES (
                :1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15
            ) RETURNING request_id INTO :16
        """, [
            ref, dept_id, svc_id, sla_id,
            fake.name(), fake.email(),
            random.choice(CHANNELS), "COMPLETED", random.choice(PRIORITIES),
            submitted, assigned, completed,
            resolution_mins, sla_deadline, 1 if compliant else 0,
            out_id
        ])
        request_ids.append((int(out_id.getvalue()[0]), compliant, resolution_mins))

        if i % 200 == 0:
            conn.commit()
            print(f"    → {i}/{count} requests inserted...")

    conn.commit()
    print(f"  ✅ Inserted {count} service requests")
    cursor.close()
    return request_ids


def insert_surveys(conn, request_ids):
    cursor = conn.cursor()
    count = 0
    for rid, compliant, resolution_mins in request_ids:
        if random.random() > 0.70:
            continue
        satisfaction = round(random.uniform(3.5, 5.0) * 2) / 2 if compliant \
                       else round(random.uniform(1.0, 3.5) * 2) / 2
        ease     = round(random.uniform(2.5, 5.0) * 2) / 2
        speed    = round(random.uniform(2.0, 5.0) * 2) / 2
        comments = fake.sentence() if random.random() > 0.5 else None
        cursor.execute("""
            INSERT INTO user_surveys (
                request_id, satisfaction_score,
                ease_of_use_score, response_speed_score, comments
            ) VALUES (:1,:2,:3,:4,:5)
        """, [rid, satisfaction, ease, speed, comments])
        count += 1
    conn.commit()
    print(f"  ✅ Inserted {count} user surveys")
    cursor.close()


def populate_dim_time(conn):
    cursor = conn.cursor()
    start   = datetime(2024, 1, 1)
    end     = datetime(2025, 12, 31)
    current = start
    count   = 0
    while current <= end:
        time_key   = int(current.strftime("%Y%m%d"))
        is_weekend = 1 if current.weekday() >= 5 else 0
        cursor.execute("""
            INSERT INTO dim_time (
                time_key, full_date, day_of_week, day_num,
                week_num, month_num, month_name,
                quarter_num, quarter_name, year_num, is_weekend
            ) VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11)
        """, [
            time_key, current, current.strftime("%A"), current.day,
            int(current.strftime("%W")), current.month, current.strftime("%B"),
            (current.month - 1) // 3 + 1, f"Q{(current.month-1)//3+1}",
            current.year, is_weekend
        ])
        current += timedelta(days=1)
        count += 1
    conn.commit()
    print(f"  ✅ Inserted {count} time dimension rows (2024-2025)")
    cursor.close()


def main():
    print("\n🚀 SDD Data Generator starting...\n")
    conn = get_connection()
    print("✅ Connected to Oracle FREEPDB1\n")

    print("📦 Inserting reference data...")
    dept_ids = insert_departments(conn)
    svc_ids  = insert_service_types(conn, dept_ids)
    sla_map  = insert_sla_definitions(conn, svc_ids)

    print("\n📋 Inserting service requests...")
    request_ids = insert_service_requests(conn, dept_ids, svc_ids, sla_map, count=1200)

    print("\n📝 Inserting user surveys...")
    insert_surveys(conn, request_ids)

    print("\n📅 Populating time dimension...")
    populate_dim_time(conn)

    conn.close()
    print("\n✅ All data generated successfully!")
    print("   • 8 departments")
    print("   • 16 service types")
    print("   • 1,200 service requests")
    print("   • ~840 user surveys")
    print("   • 731 time dimension rows")


if __name__ == "__main__":
    main()
