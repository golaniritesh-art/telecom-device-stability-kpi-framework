import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "data" / "reference"

RAW_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)


event_types = [
    "DEVICE_BOOT",
    "LTE_ATTACH_SUCCESS",
    "5G_REGISTRATION_SUCCESS",
    "NTN_REGISTRATION_SUCCESS",
    "HANDOVER_SUCCESS",
    "HANDOVER_FAILURE",
    "NETWORK_LOST",
    "NETWORK_RECOVERED",
    "MODEM_RESET",
    "CALL_DROP",
]

firmware_versions = ["S24_U1_6.1", "S24_U2_6.1", "S23_U5_6.0"]
carriers = ["Verizon", "AT&T", "T-Mobile"]
network_types = ["LTE", "5G", "NTN"]
severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
device_models = ["Galaxy S24", "Galaxy S23", "Galaxy Z Fold 5"]
cell_ids = [f"CELL_{i}" for i in range(101, 121)]


# ---------------------------------------------------
# Generate device master reference data
# ---------------------------------------------------

devices = []

for i in range(1, 51):
    devices.append(
        {
            "device_id": f"DVC-{i:03}",
            "device_model": random.choice(device_models),
            "os_version": random.choice(["Android 14", "Android 15"]),
            "region": random.choice(["US-East", "US-West", "US-Central"]),
            "active_flag": "Y",
        }
    )

device_master_df = pd.DataFrame(devices)
device_master_df.to_csv(REF_DIR / "device_master.csv", index=False)


# ---------------------------------------------------
# Generate telemetry event data
# ---------------------------------------------------

records = []
start_date = datetime.now() - timedelta(days=30)

for i in range(1, 5001):
    device = random.choice(devices)

    firmware = random.choice(firmware_versions)
    carrier = random.choice(carriers)

    # Simulate unstable firmware behavior
    if firmware == "S24_U2_6.1":
        event_weights = {
            "DEVICE_BOOT": 10,
            "LTE_ATTACH_SUCCESS": 12,
            "5G_REGISTRATION_SUCCESS": 14,
            "NTN_REGISTRATION_SUCCESS": 8,
            "HANDOVER_SUCCESS": 10,
            "HANDOVER_FAILURE": 14,
            "CALL_DROP": 10,
            "MODEM_RESET": 10,
            "NETWORK_LOST": 8,
            "NETWORK_RECOVERED": 4,
        }

    elif firmware == "S23_U5_6.0":
        event_weights = {
            "DEVICE_BOOT": 12,
            "LTE_ATTACH_SUCCESS": 18,
            "5G_REGISTRATION_SUCCESS": 10,
            "NTN_REGISTRATION_SUCCESS": 8,
            "HANDOVER_SUCCESS": 16,
            "HANDOVER_FAILURE": 8,
            "CALL_DROP": 6,
            "MODEM_RESET": 5,
            "NETWORK_LOST": 10,
            "NETWORK_RECOVERED": 7,
        }

    else:
        event_weights = {
            "DEVICE_BOOT": 12,
            "LTE_ATTACH_SUCCESS": 16,
            "5G_REGISTRATION_SUCCESS": 18,
            "NTN_REGISTRATION_SUCCESS": 8,
            "HANDOVER_SUCCESS": 16,
            "HANDOVER_FAILURE": 6,
            "CALL_DROP": 5,
            "MODEM_RESET": 5,
            "NETWORK_LOST": 8,
            "NETWORK_RECOVERED": 6,
        }

    event_type = random.choices(
        population=list(event_weights.keys()),
        weights=list(event_weights.values()),
        k=1,
    )[0]

    # Carrier-specific instability
    if carrier == "T-Mobile" and random.random() < 0.20:
        event_type = "NETWORK_LOST"

    if carrier == "Verizon" and random.random() < 0.15:
        event_type = "CALL_DROP"

    # Severity logic
    if event_type in ["MODEM_RESET", "HANDOVER_FAILURE", "NETWORK_LOST"]:
        severity = random.choice(["HIGH", "CRITICAL"])

    elif event_type in ["CALL_DROP"]:
        severity = random.choice(["MEDIUM", "HIGH"])

    else:
        severity = random.choice(severity_levels)

    # Overnight stress testing simulation
    stress_hour = random.choice([0, 1, 2, 3, 4, 22, 23])

    timestamp = start_date + timedelta(
        days=random.randint(0, 30),
        hours=stress_hour,
        minutes=random.randint(0, 59),
    )

    cpu_usage = random.randint(10, 90)
    memory_usage = random.randint(10, 90)
    battery_level = random.randint(20, 100)

    network_type = random.choice(network_types)
    cell_id = random.choice(cell_ids)
    handover_status = "FAILED" if event_type == "HANDOVER_FAILURE" else "SUCCESS"

    # Generate practical telecom KPI ranges with occasional threshold violations.
    rsrp = round(random.gauss(-95, 12), 1)
    rsrq = round(random.gauss(-10, 3), 1)
    sinr = round(random.gauss(18, 7), 1)
    latency_ms = round(random.gauss(55, 25), 1)
    jitter_ms = round(max(1, random.gauss(8, 4)), 1)
    packet_loss_pct = round(max(0, random.gauss(0.8, 0.8)), 2)
    download_throughput_mbps = round(max(1, random.gauss(180, 70)), 1)
    upload_throughput_mbps = round(max(1, random.gauss(45, 20)), 1)
    registration_time_ms = round(max(100, random.gauss(1200, 600)), 1)

    if network_type == "NTN":
        latency_ms = round(latency_ms + random.randint(60, 180), 1)

    if event_type in ["HANDOVER_FAILURE", "CALL_DROP", "NETWORK_LOST"]:
        packet_loss_pct = round(packet_loss_pct + random.uniform(1.5, 4.0), 2)
        sinr = round(sinr - random.uniform(5, 12), 1)

    if event_type in ["5G_REGISTRATION_SUCCESS", "LTE_ATTACH_SUCCESS", "NTN_REGISTRATION_SUCCESS"]:
        registration_time_ms = round(max(100, registration_time_ms), 1)

    status = "PASS"
    if (
        latency_ms > 150
        or packet_loss_pct > 2
        or registration_time_ms > 3000
        or handover_status == "FAILED"
    ):
        status = "FAIL"
    elif sinr < 10 or rsrp < -110:
        status = "WARN"

    records.append(
        {
            "event_id": str(uuid.uuid4()),
            "device_id": device["device_id"],
            "test_session_id": f"TS-{random.randint(1000, 1100)}",
            "event_timestamp": timestamp,
            "event_type": event_type,
            "firmware_version": firmware,
            "carrier": carrier,
            "network_type": network_type,
            "cell_id": cell_id,
            "rsrp": rsrp,
            "rsrq": rsrq,
            "sinr": sinr,
            "latency_ms": latency_ms,
            "jitter_ms": jitter_ms,
            "packet_loss_pct": packet_loss_pct,
            "download_throughput_mbps": download_throughput_mbps,
            "upload_throughput_mbps": upload_throughput_mbps,
            "registration_time_ms": registration_time_ms,
            "handover_status": handover_status,
            "status": status,
            "battery_level": battery_level,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "app_name": random.choice(
                ["Camera", "Messages", "Phone", "Settings", "Samsung Health"]
            ),
            "severity": severity,
            "error_code": f"ERR-{random.randint(100, 999)}",
            "region": device["region"],
        }
    )

telemetry_df = pd.DataFrame(records)


# ---------------------------------------------------
# Add intentionally bad records for validation testing
# ---------------------------------------------------

bad_records = pd.DataFrame(
    [
        {
            "event_id": None,
            "device_id": "DVC-001",
            "test_session_id": "TS-9999",
            "event_timestamp": datetime.now(),
            "event_type": "APP_CRASH",
            "firmware_version": "S24_U1_6.1",
            "carrier": "Verizon",
            "network_type": "5G",
            "cell_id": "CELL_101",
            "rsrp": -94,
            "rsrq": -9,
            "sinr": 18,
            "latency_ms": 45,
            "jitter_ms": 5,
            "packet_loss_pct": 0.2,
            "download_throughput_mbps": 210,
            "upload_throughput_mbps": 45,
            "registration_time_ms": 900,
            "handover_status": "SUCCESS",
            "status": "PASS",
            "battery_level": 50,
            "cpu_usage": 70,
            "memory_usage": 80,
            "app_name": "Camera",
            "severity": "HIGH",
            "error_code": "ERR-101",
            "region": "US-East",
        },
        {
            "event_id": str(uuid.uuid4()),
            "device_id": None,
            "test_session_id": "TS-9998",
            "event_timestamp": datetime.now(),
            "event_type": "MODEM_RESET",
            "firmware_version": None,
            "carrier": "T-Mobile",
            "network_type": "LTE",
            "cell_id": "CELL_102",
            "rsrp": -120,
            "rsrq": -14,
            "sinr": 7,
            "latency_ms": 180,
            "jitter_ms": 20,
            "packet_loss_pct": 3.5,
            "download_throughput_mbps": 12,
            "upload_throughput_mbps": 4,
            "registration_time_ms": 3500,
            "handover_status": "FAILED",
            "status": "FAIL",
            "battery_level": 120,
            "cpu_usage": 110,
            "memory_usage": 75,
            "app_name": "Phone",
            "severity": "CRITICAL",
            "error_code": "ERR-202",
            "region": "US-West",
        },
    ]
)

telemetry_df = pd.concat([telemetry_df, bad_records], ignore_index=True)

telemetry_df.to_csv(RAW_DIR / "telemetry_events.csv", index=False)


print("Sample telemetry data generated successfully.")
print(f"Telemetry records: {len(telemetry_df)}")
print(f"Device master records: {len(device_master_df)}")
print(f"Raw telemetry file: {RAW_DIR / 'telemetry_events.csv'}")
print(f"Device master file: {REF_DIR / 'device_master.csv'}")
