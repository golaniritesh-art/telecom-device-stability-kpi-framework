import pandas as pd

from src.kpi_validator import add_kpi_validation_columns, summarize_kpi_validation


def test_kpi_validator_marks_failures_and_warnings():
    df = pd.DataFrame(
        [
            {"latency_ms": 40, "packet_loss_pct": 0.1, "sinr": 20, "rsrp": -90, "registration_time_ms": 800, "handover_status": "SUCCESS"},
            {"latency_ms": 180, "packet_loss_pct": 0.1, "sinr": 20, "rsrp": -90, "registration_time_ms": 800, "handover_status": "SUCCESS"},
            {"latency_ms": 40, "packet_loss_pct": 0.1, "sinr": 8, "rsrp": -90, "registration_time_ms": 800, "handover_status": "SUCCESS"},
        ]
    )

    validated = add_kpi_validation_columns(df)

    assert list(validated["kpi_status"]) == ["PASS", "FAIL", "WARN"]


def test_kpi_summary_counts_records():
    df = pd.DataFrame(
        [
            {"latency_ms": 40, "packet_loss_pct": 0.1, "sinr": 20, "rsrp": -90, "registration_time_ms": 800, "handover_status": "SUCCESS"},
            {"latency_ms": 40, "packet_loss_pct": 3.0, "sinr": 20, "rsrp": -90, "registration_time_ms": 800, "handover_status": "SUCCESS"},
        ]
    )

    summary = summarize_kpi_validation(df)

    assert summary["total_records"] == 2
    assert summary["pass_count"] == 1
    assert summary["fail_count"] == 1
    assert summary["failure_reasons"]["packet_loss_pct > 2"] == 1
