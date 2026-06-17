from pathlib import Path

from src.log_parser import parse_modem_logs


def test_log_parser_counts_modem_events():
    log_file = Path(__file__).resolve().parent.parent / "sample_logs" / "modem_logs.txt"

    summary = parse_modem_logs(log_file)

    assert summary["registration_success_count"] == 3
    assert summary["weak_signal_count"] == 1
    assert summary["handover_failure_count"] == 1
    assert summary["call_drop_count"] == 1
    assert summary["modem_reset_count"] == 1
