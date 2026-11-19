from datetime import date
import pandas as pd


def normalise_records(data):
    """
    Accept Streamlit data_editor output (DataFrame), CSV-derived records,
    or an ordinary list of dictionaries. Always return list[dict].
    """
    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient="records")

    if isinstance(data, list):
        return data

    if data is None:
        return []

    # Support other dataframe-like objects where practical.
    if hasattr(data, "to_dict"):
        try:
            return data.to_dict(orient="records")
        except TypeError:
            pass

    raise TypeError(
        "Expected a pandas DataFrame, a list of dictionaries, or None; "
        f"received {type(data).__name__}."
    )


def demo_data():
    funds = [
        {
            "fund_id": "UNR",
            "fund_name": "Unrestricted operating cash",
            "opening_cash": 5000.0,
            "restriction": "unrestricted",
            "eligible_categories": "*",
        },
        {
            "fund_id": "YOUTH",
            "fund_name": "Youth programme grant",
            "opening_cash": 2000.0,
            "restriction": "restricted",
            "eligible_categories": "coaching,equipment,events,transport",
        },
    ]
    inflows = [
        {
            "fund_id": "YOUTH",
            "description": "Sponsor tranche 1",
            "amount": 20000.0,
            "due_date": "2026-12-15",
            "status": "committed",
            "confidence": 0.95,
        },
        {
            "fund_id": "YOUTH",
            "description": "Sponsor tranche 2",
            "amount": 15000.0,
            "due_date": "2027-02-15",
            "status": "committed",
            "confidence": 0.90,
        },
        {
            "fund_id": "UNR",
            "description": "Potential partner contribution",
            "amount": 8000.0,
            "due_date": "2027-01-15",
            "status": "pipeline",
            "confidence": 0.35,
        },
    ]
    outflows = [
        {
            "fund_id": "UNR",
            "description": "Core administration",
            "amount": 1200.0,
            "due_date": "2026-12-20",
            "category": "administration",
            "priority": "essential",
        },
        {
            "fund_id": "YOUTH",
            "description": "Coach stipends",
            "amount": 5000.0,
            "due_date": "2026-12-22",
            "category": "coaching",
            "priority": "essential",
        },
        {
            "fund_id": "YOUTH",
            "description": "Equipment",
            "amount": 6000.0,
            "due_date": "2027-01-10",
            "category": "equipment",
            "priority": "deferrable",
        },
        {
            "fund_id": "YOUTH",
            "description": "Regional event",
            "amount": 9000.0,
            "due_date": "2027-01-25",
            "category": "events",
            "priority": "discretionary",
        },
    ]
    return funds, inflows, outflows


def _month(value):
    return pd.Timestamp(value).to_period("M").to_timestamp()


def _confidence(row):
    status = str(row.get("status", "committed")).strip().lower()
    confidence = float(row.get("confidence", 1.0) or 0)

    if status == "received":
        return 1.0
    if status in {"committed", "pipeline"}:
        return max(0.0, min(1.0, confidence))
    return 0.0


def forecast(
    funds,
    inflows,
    outflows,
    months=12,
    delay_months=0,
    haircut_pct=0,
):
    """
    Produce an aggregate monthly cash forecast.

    Inputs may be DataFrames or lists of dictionaries. Expected receipts
    are weighted by their confidence value. This forecast is an estimate,
    not a guarantee that restricted funds can legally cover all expenses.
    """
    funds = normalise_records(funds)
    inflows = normalise_records(inflows)
    outflows = normalise_records(outflows)

    today = pd.Timestamp(date.today()).to_period("M").to_timestamp()
    fund_map = {
        str(f["fund_id"]): f
        for f in funds
        if pd.notna(f.get("fund_id")) and str(f.get("fund_id")).strip()
    }

    balances = {
        fid: float(fund.get("opening_cash", 0) or 0)
        for fid, fund in fund_map.items()
    }

    rows = []
    for i in range(int(months)):
        month_start = today + pd.DateOffset(months=i)
        incoming = {fid: 0.0 for fid in balances}
        outgoing = {fid: 0.0 for fid in balances}

        for item in inflows:
            fid = str(item.get("fund_id", ""))
            if fid not in incoming or pd.isna(item.get("due_date")):
                continue

            due = _month(item["due_date"]) + pd.DateOffset(
                months=int(delay_months)
            )
            if due == month_start:
                amount = float(item.get("amount", 0) or 0)
                incoming[fid] += (
                    amount
                    * _confidence(item)
                    * (1 - float(haircut_pct) / 100)
                )

        for item in outflows:
            fid = str(item.get("fund_id", ""))
            if fid not in outgoing or pd.isna(item.get("due_date")):
                continue

            if _month(item["due_date"]) == month_start:
                outgoing[fid] += float(item.get("amount", 0) or 0)

        for fid in balances:
            balances[fid] += incoming[fid] - outgoing[fid]

        total_cash = sum(balances.values())
        restricted_cash = sum(
            balances[fid]
            for fid, fund in fund_map.items()
            if str(fund.get("restriction", "restricted")).lower()
            != "unrestricted"
        )

        rows.append(
            {
                "month": month_start.strftime("%Y-%m"),
                "inflows": sum(incoming.values()),
                "outflows": sum(outgoing.values()),
                "closing_cash": total_cash,
                "restricted_cash": restricted_cash,
                "usable_cash": total_cash - restricted_cash,
            }
        )

    return pd.DataFrame(rows)


def commitment_check(funds, inflows, outflows):
    """
    Check dated commitments fund by fund.

    Funding receipts and expenditure commitments are processed chronologically.
    Restricted-fund expenditure is rejected when its category is not listed
    as eligible. Balances are never pooled between different funds.
    """
    funds = normalise_records(funds)
    inflows = normalise_records(inflows)
    outflows = normalise_records(outflows)

    fund_map = {
        str(f["fund_id"]): f
        for f in funds
        if pd.notna(f.get("fund_id")) and str(f.get("fund_id")).strip()
    }
    balances = {
        fid: float(fund.get("opening_cash", 0) or 0)
        for fid, fund in fund_map.items()
    }

    events = []

    for item in inflows:
        fid = str(item.get("fund_id", ""))
        if fid in balances and pd.notna(item.get("due_date")):
            amount = float(item.get("amount", 0) or 0) * _confidence(item)
            events.append(
                (
                    pd.Timestamp(item["due_date"]),
                    0,
                    fid,
                    amount,
                    item.get("description", "Funding"),
                    None,
                )
            )

    for item in outflows:
        fid = str(item.get("fund_id", ""))
        if fid in balances and pd.notna(item.get("due_date")):
            amount = float(item.get("amount", 0) or 0)
            events.append(
                (
                    pd.Timestamp(item["due_date"]),
                    1,
                    fid,
                    -amount,
                    item.get("description", "Commitment"),
                    item,
                )
            )

    # Funding received on a date is processed before same-day expenditure.
    events.sort(key=lambda event: (event[0], event[1]))

    issues = []
    for event_date, event_type, fid, signed_amount, label, item in events:
        if event_type == 0:
            balances[fid] += signed_amount
            continue

        fund = fund_map[fid]
        restriction = str(
            fund.get("restriction", "restricted")
        ).strip().lower()
        allowed = str(fund.get("eligible_categories", "")).strip()
        category = str(item.get("category", "")).strip()

        if (
            restriction != "unrestricted"
            and allowed != "*"
            and category not in [part.strip() for part in allowed.split(",")]
        ):
            issues.append(
                {
                    "date": event_date.date(),
                    "commitment": label,
                    "fund": fid,
                    "issue": (
                        "Category not listed as eligible for this restricted fund"
                    ),
                    "shortfall": abs(signed_amount),
                }
            )
            continue

        balances[fid] += signed_amount
        if balances[fid] < 0:
            issues.append(
                {
                    "date": event_date.date(),
                    "commitment": label,
                    "fund": fid,
                    "issue": "Insufficient projected cash in this fund",
                    "shortfall": round(-balances[fid], 2),
                }
            )

    return {
        "safe": len(issues) == 0,
        "message": (
            "No issues found by this basic rule check."
            if not issues
            else (
                f"{len(issues)} potential commitment issue(s) found. "
                "Review before approval."
            )
        ),
        "issues": issues,
    }


def scenario_forecast(
    funds,
    inflows,
    outflows,
    delay_months=0,
    haircut_pct=0,
    months=12,
):
    """Run the normal forecast with delayed and reduced expected receipts."""
    return forecast(
        funds,
        inflows,
        outflows,
        months=months,
        delay_months=delay_months,
        haircut_pct=haircut_pct,
    )
