"""
SDD Government Services - Kafka Consumer
Consumes service request events from Kafka and prints a live summary
"""

import json
from collections import defaultdict
from kafka import KafkaConsumer

KAFKA_BROKER = "localhost:9092"
TOPIC        = "sdd-service-requests"


def main():
    print(f"Connecting to Kafka topic: {TOPIC}...")
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=8000
        )
        print("Connected. Reading events...\n")

        dept_count     = defaultdict(int)
        priority_count = defaultdict(int)
        total          = 0

        for message in consumer:
            event = message.value
            dept_count[event["department"]] += 1
            priority_count[event["priority"]] += 1
            total += 1
            print(f"  Received: {event['request_ref']} | "
                  f"{event['department']} | {event['service_type']} | "
                  f"{event['priority']}")

        consumer.close()
        print(f"\n--- Summary: {total} events consumed ---")
        print("By Department:")
        for dept, count in sorted(dept_count.items()):
            print(f"  {dept}: {count}")
        print("By Priority:")
        for pri, count in sorted(priority_count.items()):
            print(f"  {pri}: {count}")

    except Exception as e:
        print(f"Kafka not reachable: {e}")


if __name__ == "__main__":
    main()
