"""
SDD Government Services - Kafka Producer
Simulates real-time streaming of new service requests to Kafka topic
"""

import json
import random
import uuid
import time
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

fake = Faker()

KAFKA_BROKER = "localhost:9092"
TOPIC        = "sdd-service-requests"

DEPARTMENTS   = ["HLTH", "TRAN", "FIN", "EDU", "HOUS", "ENV", "LAB", "INT"]
SERVICE_TYPES = ["Registration", "Appointment", "Certificate",
                 "Licensing", "Complaint", "Permit", "Document"]
CHANNELS      = ["Online Portal", "Mobile App", "Walk-in", "Call Center"]
PRIORITIES    = ["NORMAL", "HIGH", "LOW", "URGENT"]


def create_event():
    return {
        "event_id":        str(uuid.uuid4()),
        "event_type":      "SERVICE_REQUEST_CREATED",
        "timestamp":       datetime.utcnow().isoformat(),
        "request_ref":     f"REQ-{str(uuid.uuid4())[:8].upper()}",
        "department":      random.choice(DEPARTMENTS),
        "service_type":    random.choice(SERVICE_TYPES),
        "channel":         random.choice(CHANNELS),
        "priority":        random.choice(PRIORITIES),
        "requester_name":  fake.name(),
        "requester_email": fake.email(),
        "status":          "SUBMITTED"
    }


def main():
    print(f"Connecting to Kafka at {KAFKA_BROKER}...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=5000,
            max_block_ms=5000
        )
        print(f"Connected. Publishing 20 events to topic: {TOPIC}\n")
        for i in range(20):
            event = create_event()
            producer.send(TOPIC, value=event)
            print(f"  [{i+1:02d}] Sent: {event['request_ref']} | "
                  f"{event['department']} | {event['priority']}")
            time.sleep(0.3)
        producer.flush()
        producer.close()
        print(f"\nDone. 20 events published to '{TOPIC}'")
    except Exception as e:
        print(f"Kafka not reachable: {e}")


if __name__ == "__main__":
    main()
