import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import (
    commitment_check,
    demo_data,
    forecast,
    normalise_records,
    scenario_forecast,
)


def test_forecast_accepts_list_inputs():
    funds, inflows, outflows = demo_data()
    result = forecast(funds, inflows, outflows, months=3)
    assert {"month", "closing_cash", "restricted_cash", "usable_cash"}.issubset(
        result.columns
    )
    assert len(result) == 3


def test_forecast_accepts_dataframe_inputs():
    funds, inflows, outflows = demo_data()
    result = forecast(
        pd.DataFrame(funds),
        pd.DataFrame(inflows),
        pd.DataFrame(outflows),
        months=3,
    )
    assert len(result) == 3
    assert "closing_cash" in result.columns


def test_scenario_forecast_accepts_dataframe_inputs():
    funds, inflows, outflows = demo_data()
    result = scenario_forecast(
        pd.DataFrame(funds),
        pd.DataFrame(inflows),
        pd.DataFrame(outflows),
        delay_months=2,
        haircut_pct=20,
        months=4,
    )
    assert len(result) == 4


def test_commitment_check_accepts_dataframe_inputs():
    funds = pd.DataFrame(
        [
            {
                "fund_id": "R",
                "opening_cash": 1000,
                "restriction": "restricted",
                "eligible_categories": "coaching",
            }
        ]
    )
    inflows = pd.DataFrame()
    outflows = pd.DataFrame(
        [
            {
                "fund_id": "R",
                "description": "Office rent",
                "amount": 100,
                "due_date": "2026-12-01",
                "category": "rent",
                "priority": "essential",
            }
        ]
    )
    result = commitment_check(funds, inflows, outflows)
    assert not result["safe"]
    assert "not listed as eligible" in result["issues"][0]["issue"].lower()


def test_normalise_records_accepts_none_and_dataframe():
    assert normalise_records(None) == []
    df = pd.DataFrame([{"fund_id": "A"}])
    assert normalise_records(df) == [{"fund_id": "A"}]
