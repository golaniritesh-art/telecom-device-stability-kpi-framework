import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "telemetry.db"


@st.cache_data
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        raw_df = pd.read_sql_query("SELECT * FROM raw_device_telemetry", conn)
        clean_df = pd.read_sql_query("SELECT * FROM clean_telemetry_events", conn)
        rejected_df = pd.read_sql_query("SELECT * FROM rejected_telemetry_events", conn)
        summary_df = pd.read_sql_query("SELECT * FROM daily_stability_summary", conn)
        son_df = pd.read_sql_query("SELECT * FROM son_recommendations", conn)

    clean_df["event_timestamp"] = pd.to_datetime(clean_df["event_timestamp"])
    clean_df["event_date"] = pd.to_datetime(clean_df["event_date"])
    return raw_df, clean_df, rejected_df, summary_df, son_df


def safe_rate(success_count, total_count):
    if total_count == 0:
        return 0
    return round((success_count / total_count) * 100, 2)


def build_firmware_stability_summary(df):
    """Summarize whether each firmware looks stable from device and network KPIs."""
    if df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby("firmware_version")
        .agg(
            total_events=("event_id", "count"),
            devices_tested=("device_id", "nunique"),
            kpi_failures=("kpi_status", lambda x: (x == "FAIL").sum()),
            kpi_warnings=("kpi_status", lambda x: (x == "WARN").sum()),
            modem_resets=("event_type", lambda x: (x == "MODEM_RESET").sum()),
            call_drops=("event_type", lambda x: (x == "CALL_DROP").sum()),
            network_lost=("event_type", lambda x: (x == "NETWORK_LOST").sum()),
            handover_failures=("event_type", lambda x: (x == "HANDOVER_FAILURE").sum()),
            avg_latency_ms=("latency_ms", "mean"),
            avg_packet_loss_pct=("packet_loss_pct", "mean"),
        )
        .reset_index()
    )

    summary["kpi_fail_rate_pct"] = (summary["kpi_failures"] / summary["total_events"] * 100).round(2)
    summary["modem_reset_rate_pct"] = (summary["modem_resets"] / summary["total_events"] * 100).round(2)
    summary["call_drop_rate_pct"] = (summary["call_drops"] / summary["total_events"] * 100).round(2)
    summary["stability_score"] = (
        100
        - summary["kpi_fail_rate_pct"] * 1.2
        - summary["modem_reset_rate_pct"] * 2.0
        - summary["call_drop_rate_pct"] * 1.5
        - (summary["handover_failures"] / summary["total_events"] * 100) * 1.2
    ).clip(lower=0).round(2)

    summary["firmware_verdict"] = "STABLE"
    summary.loc[
        (summary["stability_score"] < 85)
        | (summary["modem_reset_rate_pct"] > 5)
        | (summary["kpi_fail_rate_pct"] > 10),
        "firmware_verdict",
    ] = "NEEDS INVESTIGATION"
    summary.loc[
        (summary["stability_score"] < 70)
        | (summary["modem_reset_rate_pct"] > 15)
        | (summary["kpi_fail_rate_pct"] > 25),
        "firmware_verdict",
    ] = "UNSTABLE"

    return summary.sort_values(by="stability_score", ascending=True)


st.set_page_config(
    page_title="Device Firmware Stability Dashboard",
    layout="wide",
)

st.title("Device Firmware Stability Dashboard")
st.caption("Firmware stability, modem reset behavior, LTE/5G/NTN KPI validation, and network diagnostics")

raw_df, clean_df, rejected_df, summary_df, son_df = load_data()

st.sidebar.header("Filters")

carrier_filter = st.sidebar.multiselect(
    "Carrier",
    options=sorted(clean_df["carrier"].unique()),
    default=sorted(clean_df["carrier"].unique()),
)

network_filter = st.sidebar.multiselect(
    "Network Type",
    options=sorted(clean_df["network_type"].unique()),
    default=sorted(clean_df["network_type"].unique()),
)

firmware_filter = st.sidebar.multiselect(
    "Firmware Version",
    options=sorted(clean_df["firmware_version"].unique()),
    default=sorted(clean_df["firmware_version"].unique()),
)

filtered_df = clean_df[
    clean_df["carrier"].isin(carrier_filter)
    & clean_df["network_type"].isin(network_filter)
    & clean_df["firmware_version"].isin(firmware_filter)
]

fail_count = int((filtered_df["kpi_status"] == "FAIL").sum())
warn_count = int((filtered_df["kpi_status"] == "WARN").sum())
network_health_score = max(0, round(100 - ((fail_count * 1.5 + warn_count * 0.5) / max(len(filtered_df), 1) * 100), 2))

registration_events = ["LTE_ATTACH_SUCCESS", "5G_REGISTRATION_SUCCESS", "NTN_REGISTRATION_SUCCESS"]
registration_success_rate = safe_rate(filtered_df["event_type"].isin(registration_events).sum(), len(filtered_df))
handover_total = filtered_df["event_type"].isin(["HANDOVER_SUCCESS", "HANDOVER_FAILURE"]).sum()
handover_success_rate = safe_rate((filtered_df["event_type"] == "HANDOVER_SUCCESS").sum(), handover_total)
avg_latency = round(filtered_df["latency_ms"].mean(), 2) if not filtered_df.empty else 0
weak_signal_count = int(((filtered_df["rsrp"] < -110) | (filtered_df["sinr"] < 10)).sum())
firmware_summary = build_firmware_stability_summary(filtered_df)

st.header("Firmware Stability Decision")

if firmware_summary.empty:
    st.warning("No records match the selected filters.")
else:
    worst_firmware = firmware_summary.iloc[0]
    stable_count = int((firmware_summary["firmware_verdict"] == "STABLE").sum())
    investigation_count = int((firmware_summary["firmware_verdict"] == "NEEDS INVESTIGATION").sum())
    unstable_count = int((firmware_summary["firmware_verdict"] == "UNSTABLE").sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Worst Firmware", worst_firmware["firmware_version"])
    c2.metric("Worst Stability Score", worst_firmware["stability_score"])
    c3.metric("Stable Builds", stable_count)
    c4.metric("Needs Investigation", investigation_count)
    c5.metric("Unstable Builds", unstable_count)

    st.subheader("Firmware Stability Summary")
    st.dataframe(
        firmware_summary[
            [
                "firmware_version",
                "firmware_verdict",
                "stability_score",
                "total_events",
                "devices_tested",
                "kpi_fail_rate_pct",
                "modem_reset_rate_pct",
                "call_drop_rate_pct",
                "modem_resets",
                "call_drops",
                "network_lost",
                "handover_failures",
                "avg_latency_ms",
                "avg_packet_loss_pct",
            ]
        ],
        use_container_width=True,
    )

    st.subheader("Firmware Stability Score")
    st.bar_chart(
        firmware_summary.sort_values(by="stability_score", ascending=False),
        x="firmware_version",
        y="stability_score",
    )

    st.subheader("Modem Resets by Firmware")
    st.bar_chart(firmware_summary, x="firmware_version", y="modem_resets")

    st.subheader("KPI Fail Rate by Firmware")
    st.bar_chart(firmware_summary, x="firmware_version", y="kpi_fail_rate_pct")

st.header("Network Health Diagnostics")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Network Health Score", network_health_score)
col2.metric("Registration Success Rate", f"{registration_success_rate}%")
col3.metric("Handover Success Rate", f"{handover_success_rate}%")
col4.metric("Average Latency", f"{avg_latency} ms")
col5.metric("Weak Signal Count", weak_signal_count)

col6, col7, col8, col9 = st.columns(4)
col6.metric("Raw Records", len(raw_df))
col7.metric("Clean Records", len(clean_df))
col8.metric("Rejected Records", len(rejected_df))
col9.metric("KPI Failures", fail_count)

st.header("KPI Trends")

packet_loss_trend = (
    filtered_df.groupby("event_date", as_index=False)["packet_loss_pct"]
    .mean()
    .rename(columns={"packet_loss_pct": "avg_packet_loss_pct"})
)
st.subheader("Packet Loss Trend")
st.line_chart(packet_loss_trend, x="event_date", y="avg_packet_loss_pct")

st.subheader("KPI Violations by Carrier")
carrier_violations = (
    filtered_df[filtered_df["kpi_status"] == "FAIL"]
    .groupby("carrier")
    .size()
    .reset_index(name="failure_count")
)
st.bar_chart(carrier_violations, x="carrier", y="failure_count")

st.subheader("KPI Violations by Network Type")
network_violations = (
    filtered_df[filtered_df["kpi_status"] == "FAIL"]
    .groupby("network_type")
    .size()
    .reset_index(name="failure_count")
)
st.bar_chart(network_violations, x="network_type", y="failure_count")

st.header("SON Recommendations")
if son_df.empty:
    st.info("No SON recommendations generated for the current data set.")
else:
    st.dataframe(son_df, use_container_width=True)

st.header("Problematic KPI Records")
problem_records = filtered_df[filtered_df["kpi_status"].isin(["WARN", "FAIL"])]
st.dataframe(
    problem_records[
        [
            "event_timestamp",
            "device_id",
            "carrier",
            "network_type",
            "cell_id",
            "event_type",
            "kpi_status",
            "failure_reasons",
            "rsrp",
            "sinr",
            "latency_ms",
            "packet_loss_pct",
            "registration_time_ms",
            "handover_status",
        ]
    ].head(200),
    use_container_width=True,
)

st.header("Backend Reconciliation")
recon_status = "PASS" if len(raw_df) == len(clean_df) + len(rejected_df) else "FAIL"
st.dataframe(
    pd.DataFrame(
        {
            "Metric": ["Raw Records", "Clean Records", "Rejected Records", "Clean + Rejected", "Status"],
            "Value": [len(raw_df), len(clean_df), len(rejected_df), len(clean_df) + len(rejected_df), recon_status],
        }
    ),
    use_container_width=True,
)
