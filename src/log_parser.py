from pathlib import Path


def parse_modem_logs(log_file):
    """Parse modem logs and return counts used by validation dashboards."""
    text = Path(log_file).read_text(encoding="utf-8")
    lines = text.splitlines()

    return {
        "registration_success_count": sum("REGISTRATION_SUCCESS" in line or "LTE_ATTACH_SUCCESS" in line for line in lines),
        "weak_signal_count": sum("WEAK_SIGNAL" in line for line in lines),
        "handover_failure_count": sum("HANDOVER_FAILURE" in line for line in lines),
        "call_drop_count": sum("CALL_DROP" in line for line in lines),
        "modem_reset_count": sum("MODEM_RESET" in line for line in lines),
    }
