import pandas as pd

from src.son_recommendation_engine import generate_son_recommendations


def test_son_recommendations_generated_for_problematic_cell():
    df = pd.DataFrame(
        [
            {"cell_id": "CELL_101", "handover_status": "FAILED", "packet_loss_pct": 3.0, "rsrp": -116, "sinr": 7, "latency_ms": 170, "registration_time_ms": 3500},
            {"cell_id": "CELL_101", "handover_status": "FAILED", "packet_loss_pct": 2.5, "rsrp": -112, "sinr": 8, "latency_ms": 190, "registration_time_ms": 3300},
            {"cell_id": "CELL_102", "handover_status": "SUCCESS", "packet_loss_pct": 0.1, "rsrp": -90, "sinr": 22, "latency_ms": 40, "registration_time_ms": 700},
        ]
    )

    recommendations = generate_son_recommendations(df)

    assert not recommendations.empty
    assert "CELL_101" in recommendations["cell_id"].tolist()
    assert "High packet loss" in recommendations["issue"].tolist()
