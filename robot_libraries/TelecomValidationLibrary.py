import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "telemetry.db"


class TelecomValidationLibrary:
    """Small Robot Framework library for telecom KPI smoke checks."""

    def _query_one(self, query):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchone()[0]

    def get_5g_registration_success_rate(self):
        return self._success_rate("'5G_REGISTRATION_SUCCESS'", "network_type = '5G'")

    def get_lte_attach_success_rate(self):
        return self._success_rate("'LTE_ATTACH_SUCCESS'", "network_type = 'LTE'")

    def get_ntn_average_latency(self):
        return float(self._query_one("SELECT AVG(latency_ms) FROM clean_telemetry_events WHERE network_type = 'NTN'"))

    def get_handover_success_rate(self):
        total = self._query_one("SELECT COUNT(*) FROM clean_telemetry_events WHERE event_type IN ('HANDOVER_SUCCESS', 'HANDOVER_FAILURE')")
        if total == 0:
            return 0
        success = self._query_one("SELECT COUNT(*) FROM clean_telemetry_events WHERE event_type = 'HANDOVER_SUCCESS'")
        return round((success / total) * 100, 2)

    def get_kpi_failure_count(self):
        return int(self._query_one("SELECT COUNT(*) FROM clean_telemetry_events WHERE kpi_status = 'FAIL'"))

    def get_son_recommendation_count(self):
        return int(self._query_one("SELECT COUNT(*) FROM son_recommendations"))

    def summarize_csv_scenario(self, csv_path):
        """Read a scenario CSV and return counts for data-driven Robot tests."""
        df = pd.read_csv(BASE_DIR / csv_path)

        return {
            "total_records": int(len(df)),
            "pass_count": int((df["status"] == "PASS").sum()),
            "warn_count": int((df["status"] == "WARN").sum()),
            "fail_count": int((df["status"] == "FAIL").sum()),
            "modem_reset_count": int((df["event_type"] == "MODEM_RESET").sum()),
            "network_lost_count": int((df["event_type"] == "NETWORK_LOST").sum()),
            "handover_failure_count": int((df["event_type"] == "HANDOVER_FAILURE").sum()),
            "call_drop_count": int((df["event_type"] == "CALL_DROP").sum()),
            "avg_latency_ms": round(float(df["latency_ms"].mean()), 2),
            "avg_packet_loss_pct": round(float(df["packet_loss_pct"].mean()), 2),
        }

    def _success_rate(self, success_event, filter_clause):
        total = self._query_one(f"SELECT COUNT(*) FROM clean_telemetry_events WHERE {filter_clause}")
        if total == 0:
            return 0
        success = self._query_one(
            f"SELECT COUNT(*) FROM clean_telemetry_events WHERE {filter_clause} AND event_type = {success_event}"
        )
        return round((success / total) * 100, 2)
