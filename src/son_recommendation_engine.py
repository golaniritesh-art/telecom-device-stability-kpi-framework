import pandas as pd


def generate_son_recommendations(telemetry_df):
    """Create simple rule-based SON recommendations by cell."""
    recommendations = []

    if telemetry_df.empty:
        return pd.DataFrame(
            columns=["cell_id", "issue", "severity", "recommendation"]
        )

    for cell_id, cell_df in telemetry_df.groupby("cell_id"):
        total = len(cell_df)
        handover_fail_rate = (cell_df["handover_status"].astype(str).str.upper() == "FAILED").sum() / total
        high_packet_loss_rate = (cell_df["packet_loss_pct"] > 2).sum() / total
        weak_rsrp_rate = (cell_df["rsrp"] < -110).sum() / total
        low_sinr_rate = (cell_df["sinr"] < 10).sum() / total
        high_latency_rate = (cell_df["latency_ms"] > 150).sum() / total
        slow_registration_rate = (cell_df["registration_time_ms"] > 3000).sum() / total

        if handover_fail_rate >= 0.10:
            recommendations.append(_row(cell_id, "High handover failure rate", "HIGH", "Review neighbor relations / mobility parameters"))
        if high_packet_loss_rate >= 0.15:
            recommendations.append(_row(cell_id, "High packet loss", "HIGH", "Check backhaul congestion"))
        if weak_rsrp_rate >= 0.15:
            recommendations.append(_row(cell_id, "Weak RSRP", "MEDIUM", "Coverage optimization"))
        if low_sinr_rate >= 0.15:
            recommendations.append(_row(cell_id, "Low SINR", "MEDIUM", "Interference investigation"))
        if high_latency_rate >= 0.15:
            recommendations.append(_row(cell_id, "High latency", "HIGH", "Capacity or routing optimization"))
        if slow_registration_rate >= 0.05:
            recommendations.append(_row(cell_id, "Repeated registration failures", "HIGH", "Core/RAN signaling investigation"))

    return pd.DataFrame(recommendations)


def _row(cell_id, issue, severity, recommendation):
    return {
        "cell_id": cell_id,
        "issue": issue,
        "severity": severity,
        "recommendation": recommendation,
    }
