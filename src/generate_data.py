import argparse
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "data" / "reference"
SCENARIO_DIR = BASE_DIR / "data" / "scenarios"

RAW_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)
SCENARIO_DIR.mkdir(parents=True, exist_ok=True)


FIRMWARE_VERSIONS = ["S24_U1_6.1", "S24_U2_6.1", "S23_U5_6.0"]
CARRIERS = ["Verizon", "AT&T", "T-Mobile"]
NETWORK_TYPES = ["LTE", "5G", "NTN"]
DEVICE_MODELS = ["Galaxy S24", "Galaxy S23", "Galaxy Z Fold 5"]
CELL_IDS = [f"CELL_{i}" for i in range(101, 121)]
REGISTRATION_EVENTS = [
    "LTE_ATTACH_SUCCESS",
    "5G_REGISTRATION_SUCCESS",
    "NTN_REGISTRATION_SUCCESS",
]


def build_device_master():
    """Create a small device reference table used by all scenarios."""
    devices = []

    for i in range(1, 51):
        devices.append(
            {
                "device_id": f"DVC-{i:03}",
                "device_model": random.choice(DEVICE_MODELS),
                "os_version": random.choice(["Android 14", "Android 15"]),
                "region": random.choice(["US-East", "US-West", "US-Central"]),
                "active_flag": "Y",
            }
        )

    return pd.DataFrame(devices)


def calculate_status(event_type, latency_ms, packet_loss_pct, sinr, rsrp, registration_time_ms, handover_status):
    """Apply the same simple status rules used by the KPI validator."""
    if (
        latency_ms > 150
        or packet_loss_pct > 2
        or registration_time_ms > 3000
        or handover_status == "FAILED"
        or event_type in ["MODEM_RESET", "CALL_DROP", "NETWORK_LOST"]
    ):
        return "FAIL"

    if sinr < 10 or rsrp < -110:
        return "WARN"

    return "PASS"


def choose_event_type(scenario):
    if scenario == "stable":
        return random.choice(
            [
                "DEVICE_BOOT",
                "LTE_ATTACH_SUCCESS",
                "5G_REGISTRATION_SUCCESS",
                "NTN_REGISTRATION_SUCCESS",
                "HANDOVER_SUCCESS",
                "NETWORK_RECOVERED",
            ]
        )

    if scenario == "modem_resets":
        return random.choices(
            population=[
                "DEVICE_BOOT",
                "LTE_ATTACH_SUCCESS",
                "5G_REGISTRATION_SUCCESS",
                "HANDOVER_SUCCESS",
                "MODEM_RESET",
            ],
            weights=[8, 14, 14, 14, 50],
            k=1,
        )[0]

    if scenario == "network_instability":
        return random.choices(
            population=[
                "LTE_ATTACH_SUCCESS",
                "5G_REGISTRATION_SUCCESS",
                "NTN_REGISTRATION_SUCCESS",
                "HANDOVER_SUCCESS",
                "HANDOVER_FAILURE",
                "CALL_DROP",
                "NETWORK_LOST",
                "NETWORK_RECOVERED",
            ],
            weights=[8, 8, 5, 10, 22, 18, 24, 5],
            k=1,
        )[0]

    return random.choices(
        population=[
            "DEVICE_BOOT",
            "LTE_ATTACH_SUCCESS",
            "5G_REGISTRATION_SUCCESS",
            "NTN_REGISTRATION_SUCCESS",
            "HANDOVER_SUCCESS",
            "HANDOVER_FAILURE",
            "CALL_DROP",
            "MODEM_RESET",
            "NETWORK_LOST",
            "NETWORK_RECOVERED",
        ],
        weights=[10, 14, 15, 8, 14, 9, 8, 7, 10, 5],
        k=1,
    )[0]


def generate_kpis(scenario, event_type, network_type):
    """Generate KPI values for each scenario."""
    if scenario == "stable":
        rsrp = round(random.uniform(-100, -82), 1)
        rsrq = round(random.uniform(-10, -6), 1)
        sinr = round(random.uniform(15, 28), 1)
        latency_ms = round(random.uniform(25, 85), 1)
        jitter_ms = round(random.uniform(1, 8), 1)
        packet_loss_pct = round(random.uniform(0, 0.6), 2)
        download = round(random.uniform(160, 380), 1)
        upload = round(random.uniform(35, 95), 1)
        registration_time_ms = round(random.uniform(350, 1300), 1)
        handover_status = "SUCCESS"
        return rsrp, rsrq, sinr, latency_ms, jitter_ms, packet_loss_pct, download, upload, registration_time_ms, handover_status

    rsrp = round(random.gauss(-95, 12), 1)
    rsrq = round(random.gauss(-10, 3), 1)
    sinr = round(random.gauss(18, 7), 1)
    latency_ms = round(random.gauss(55, 25), 1)
    jitter_ms = round(max(1, random.gauss(8, 4)), 1)
    packet_loss_pct = round(max(0, random.gauss(0.8, 0.8)), 2)
    download = round(max(1, random.gauss(180, 70)), 1)
    upload = round(max(1, random.gauss(45, 20)), 1)
    registration_time_ms = round(max(100, random.gauss(1200, 600)), 1)
    handover_status = "FAILED" if event_type == "HANDOVER_FAILURE" else "SUCCESS"

    if network_type == "NTN":
        latency_ms = round(latency_ms + random.randint(60, 180), 1)

    if scenario == "modem_resets" and event_type == "MODEM_RESET":
        latency_ms = round(random.uniform(80, 180), 1)
        jitter_ms = round(random.uniform(12, 35), 1)
        packet_loss_pct = round(random.uniform(0.5, 3.0), 2)
        download = round(random.uniform(10, 90), 1)
        upload = round(random.uniform(2, 25), 1)

    if scenario == "network_instability" or event_type in ["HANDOVER_FAILURE", "CALL_DROP", "NETWORK_LOST"]:
        rsrp = round(random.uniform(-122, -104), 1)
        sinr = round(random.uniform(2, 11), 1)
        latency_ms = round(random.uniform(120, 260), 1)
        jitter_ms = round(random.uniform(18, 60), 1)
        packet_loss_pct = round(random.uniform(2.5, 8.0), 2)
        download = round(random.uniform(3, 80), 1)
        upload = round(random.uniform(1, 18), 1)

    return rsrp, rsrq, sinr, latency_ms, jitter_ms, packet_loss_pct, download, upload, registration_time_ms, handover_status


def generate_telemetry(devices_df, scenario, records):
    start_date = datetime.now() - timedelta(days=30)
    rows = []
    devices = devices_df.to_dict("records")

    for _ in range(records):
        device = random.choice(devices)
        event_type = choose_event_type(scenario)
        carrier = random.choice(CARRIERS)
        network_type = random.choice(NETWORK_TYPES)
        firmware_version = random.choice(FIRMWARE_VERSIONS)

        if scenario == "stable":
            firmware_version = "S24_U1_6.1"
        elif scenario == "modem_resets":
            firmware_version = random.choices(
                population=["S24_U2_6.1", "S24_U1_6.1", "S23_U5_6.0"],
                weights=[70, 15, 15],
                k=1,
            )[0]

        if event_type == "LTE_ATTACH_SUCCESS":
            network_type = "LTE"
        elif event_type == "5G_REGISTRATION_SUCCESS":
            network_type = "5G"
        elif event_type == "NTN_REGISTRATION_SUCCESS":
            network_type = "NTN"

        timestamp = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.choice([0, 1, 2, 3, 4, 22, 23]),
            minutes=random.randint(0, 59),
        )

        (
            rsrp,
            rsrq,
            sinr,
            latency_ms,
            jitter_ms,
            packet_loss_pct,
            download,
            upload,
            registration_time_ms,
            handover_status,
        ) = generate_kpis(scenario, event_type, network_type)

        status = calculate_status(
            event_type,
            latency_ms,
            packet_loss_pct,
            sinr,
            rsrp,
            registration_time_ms,
            handover_status,
        )
        severity = "LOW" if status == "PASS" else random.choice(["HIGH", "CRITICAL"])

        rows.append(
            {
                "event_id": str(uuid.uuid4()),
                "device_id": device["device_id"],
                "test_session_id": f"TS-{random.randint(1000, 1100)}",
                "event_timestamp": timestamp,
                "event_type": event_type,
                "firmware_version": firmware_version,
                "carrier": carrier,
                "network_type": network_type,
                "cell_id": random.choice(CELL_IDS),
                "rsrp": rsrp,
                "rsrq": rsrq,
                "sinr": sinr,
                "latency_ms": latency_ms,
                "jitter_ms": jitter_ms,
                "packet_loss_pct": packet_loss_pct,
                "download_throughput_mbps": download,
                "upload_throughput_mbps": upload,
                "registration_time_ms": registration_time_ms,
                "handover_status": handover_status,
                "status": status,
                "battery_level": random.randint(20, 100),
                "cpu_usage": random.randint(10, 90),
                "memory_usage": random.randint(10, 90),
                "app_name": random.choice(["Camera", "Messages", "Phone", "Settings", "Samsung Health"]),
                "severity": severity,
                "error_code": f"ERR-{random.randint(100, 999)}",
                "region": device["region"],
            }
        )

    return pd.DataFrame(rows)


def add_bad_records(telemetry_df):
    """Keep two rejected records for the ETL data-quality tests."""
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

    return pd.concat([telemetry_df, bad_records], ignore_index=True)


def save_default_dataset(devices_df, scenario, records):
    telemetry_df = generate_telemetry(devices_df, scenario, records)
    telemetry_df = add_bad_records(telemetry_df)
    telemetry_df.to_csv(RAW_DIR / "telemetry_events.csv", index=False)
    devices_df.to_csv(REF_DIR / "device_master.csv", index=False)

    print("Telemetry data generated successfully.")
    print(f"Scenario: {scenario}")
    print(f"Telemetry records: {len(telemetry_df)}")
    print(f"Device master records: {len(devices_df)}")
    print(f"Raw telemetry file: {RAW_DIR / 'telemetry_events.csv'}")
    print(f"Device master file: {REF_DIR / 'device_master.csv'}")


def save_all_scenario_datasets(devices_df, records):
    scenario_files = {
        "stable": "stable_firmware_all_pass.csv",
        "modem_resets": "modem_reset_issue.csv",
        "network_instability": "network_instability.csv",
    }

    devices_df.to_csv(REF_DIR / "device_master.csv", index=False)

    for scenario, file_name in scenario_files.items():
        telemetry_df = generate_telemetry(devices_df, scenario, records)
        telemetry_df.to_csv(SCENARIO_DIR / file_name, index=False)
        print(f"Created {scenario} dataset: {SCENARIO_DIR / file_name}")


def main():
    parser = argparse.ArgumentParser(description="Generate telecom device telemetry datasets.")
    parser.add_argument(
        "--scenario",
        choices=["mixed", "stable", "modem_resets", "network_instability", "all"],
        default="mixed",
        help="Dataset type to generate. Use 'all' to create the three presentation datasets.",
    )
    parser.add_argument("--records", type=int, default=5000, help="Number of records per dataset.")
    args = parser.parse_args()

    random.seed(42)
    devices_df = build_device_master()

    if args.scenario == "all":
        save_all_scenario_datasets(devices_df, args.records)
    else:
        save_default_dataset(devices_df, args.scenario, args.records)


if __name__ == "__main__":
    main()
