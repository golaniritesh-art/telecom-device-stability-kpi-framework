import pandas as pd


def validate_kpi_record(record):
    """Validate one telemetry record and return status plus readable reasons."""
    reasons = []
    status = "PASS"

    if record.get("latency_ms", 0) > 150:
        reasons.append("latency_ms > 150")
    if record.get("packet_loss_pct", 0) > 2:
        reasons.append("packet_loss_pct > 2")
    if record.get("registration_time_ms", 0) > 3000:
        reasons.append("registration_time_ms > 3000")
    if str(record.get("handover_status", "")).upper() == "FAILED":
        reasons.append("handover_status == FAILED")

    if reasons:
        status = "FAIL"
    elif record.get("sinr", 99) < 10:
        status = "WARN"
        reasons.append("sinr < 10")
    elif record.get("rsrp", 0) < -110:
        status = "WARN"
        reasons.append("rsrp < -110")

    return status, reasons


def add_kpi_validation_columns(telemetry_df):
    """Add kpi_status and failure_reasons columns to a telemetry DataFrame."""
    df = telemetry_df.copy()
    results = df.apply(lambda row: validate_kpi_record(row.to_dict()), axis=1)
    df["kpi_status"] = results.apply(lambda value: value[0])
    df["failure_reasons"] = results.apply(lambda value: "; ".join(value[1]))
    return df


def summarize_kpi_validation(telemetry_df):
    """Return high-level KPI validation counts and failure reason frequencies."""
    if telemetry_df.empty:
        return {
            "total_records": 0,
            "pass_count": 0,
            "warn_count": 0,
            "fail_count": 0,
            "failure_reasons": {},
        }

    validated_df = add_kpi_validation_columns(telemetry_df)
    reason_counts = {}

    for reasons in validated_df["failure_reasons"]:
        for reason in [item.strip() for item in str(reasons).split(";") if item.strip()]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "total_records": int(len(validated_df)),
        "pass_count": int((validated_df["kpi_status"] == "PASS").sum()),
        "warn_count": int((validated_df["kpi_status"] == "WARN").sum()),
        "fail_count": int((validated_df["kpi_status"] == "FAIL").sum()),
        "failure_reasons": reason_counts,
    }


def summary_to_dataframe(summary):
    """Convert a KPI summary dictionary into a compact reporting DataFrame."""
    return pd.DataFrame(
        [
            {"metric": "total_records", "value": summary["total_records"]},
            {"metric": "pass_count", "value": summary["pass_count"]},
            {"metric": "warn_count", "value": summary["warn_count"]},
            {"metric": "fail_count", "value": summary["fail_count"]},
        ]
    )
