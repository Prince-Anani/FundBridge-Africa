import pandas as pd
import streamlit as st

from engine import (
    commitment_check,
    demo_data,
    forecast,
    normalise_records,
    scenario_forecast,
)

st.set_page_config(
    page_title="FundBridge Africa",
    page_icon="💧",
    layout="wide",
)

st.title("FundBridge Africa")
st.caption("Funding-aware liquidity and programme commitment safety")
st.info(
    "Prototype only. Use fictional or anonymised data. "
    "This is not accounting, lending, investment or legal advice."
)

# Initialise session data once. Streamlit's data_editor returns DataFrames,
# so the financial engine is designed to accept both DataFrames and records.
if "funds" not in st.session_state:
    (
        st.session_state.funds,
        st.session_state.inflows,
        st.session_state.outflows,
    ) = demo_data()

with st.sidebar:
    st.header("Organisation")
    organisation = st.text_input(
        "Organisation name",
        "West Africa Development Programme",
    )
    currency = st.selectbox(
        "Display currency",
        ["USD", "NGN", "GHS", "XOF", "EUR", "GBP"],
    )
    st.caption("All amounts must use the same currency in this prototype.")

tabs = st.tabs(
    ["Dashboard", "Funding", "Commitments", "Stress test", "Data & export"]
)

with tabs[0]:
    st.subheader("Liquidity overview")

    forecast_df = forecast(
        st.session_state.funds,
        st.session_state.inflows,
        st.session_state.outflows,
        months=12,
    )
    funds_records = normalise_records(st.session_state.funds)
    opening_cash = sum(
        float(fund.get("opening_cash", 0) or 0)
        for fund in funds_records
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Opening cash", f"{currency} {opening_cash:,.2f}")
    col2.metric(
        "Lowest projected cash",
        (
            f"{currency} {forecast_df['closing_cash'].min():,.2f}"
            if not forecast_df.empty
            else "—"
        ),
    )
    col3.metric(
        "Months below zero",
        (
            int((forecast_df["closing_cash"] < 0).sum())
            if not forecast_df.empty
            else 0
        ),
    )

    if not forecast_df.empty:
        st.line_chart(
            forecast_df.set_index("month")[["closing_cash", "usable_cash"]]
        )
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    st.caption(
        "Usable cash is an aggregate estimate after subtracting restricted "
        "balances. Confirm legal restrictions and eligible costs with the "
        "funder and your finance officer."
    )

with tabs[1]:
    st.subheader("Funding sources and tranches")
    st.write(
        "Record each expected receipt separately. A pledged or speculative "
        "amount is not cash in the bank."
    )

    edited_funds = st.data_editor(
        pd.DataFrame(normalise_records(st.session_state.funds)),
        num_rows="dynamic",
        use_container_width=True,
        key="fund_editor",
    )
    edited_inflows = st.data_editor(
        pd.DataFrame(normalise_records(st.session_state.inflows)),
        num_rows="dynamic",
        use_container_width=True,
        key="inflow_editor",
    )

    st.session_state.funds = edited_funds
    st.session_state.inflows = edited_inflows

    st.download_button(
        "Download funding CSV",
        data=pd.DataFrame(
            normalise_records(st.session_state.inflows)
        ).to_csv(index=False),
        file_name="funding.csv",
        mime="text/csv",
    )

with tabs[2]:
    st.subheader("Programme commitments")
    st.write(
        "Assign each expense to a fund. Use 'unrestricted' only when the "
        "organisation is legally free to use the money for that expense."
    )

    edited_outflows = st.data_editor(
        pd.DataFrame(normalise_records(st.session_state.outflows)),
        num_rows="dynamic",
        use_container_width=True,
        key="outflow_editor",
    )
    st.session_state.outflows = edited_outflows

    if st.button("Check commitment safety", type="primary"):
        result = commitment_check(
            st.session_state.funds,
            st.session_state.inflows,
            st.session_state.outflows,
        )
        if result["safe"]:
            st.success(result["message"])
        else:
            st.error(result["message"])

        issues_df = pd.DataFrame(result["issues"])
        if issues_df.empty:
            st.success("There are no commitment issues under the current rules.")
        else:
            st.dataframe(issues_df, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Funding-delay stress test")
    delay = st.slider(
        "Delay expected funding by (months)",
        min_value=0,
        max_value=6,
        value=2,
    )
    haircut = st.slider(
        "Reduce expected receipts by (%)",
        min_value=0,
        max_value=100,
        value=20,
    )

    stressed_df = scenario_forecast(
        st.session_state.funds,
        st.session_state.inflows,
        st.session_state.outflows,
        delay_months=delay,
        haircut_pct=haircut,
        months=12,
    )
    base_df = forecast(
        st.session_state.funds,
        st.session_state.inflows,
        st.session_state.outflows,
        months=12,
    )

    comparison = base_df[["month", "closing_cash"]].merge(
        stressed_df[["month", "closing_cash"]],
        on="month",
        suffixes=("_base", "_stress"),
    )

    st.line_chart(comparison.set_index("month"))
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    if not stressed_df.empty and (stressed_df["closing_cash"] < 0).any():
        st.warning(
            "This scenario produces a negative projected aggregate cash "
            "balance. Review commitments, funding assumptions and timing."
        )
    else:
        st.success(
            "No negative aggregate closing balance in this scenario. "
            "This does not guarantee that every fund can pay every expense."
        )

with tabs[4]:
    st.subheader("Import and export")
    st.write(
        "Upload CSV files to replace the corresponding table. "
        "Use the sample CSV files as templates."
    )

    uploaded_funds = st.file_uploader(
        "Upload funds.csv", type="csv", key="upload_funds"
    )
    uploaded_inflows = st.file_uploader(
        "Upload funding.csv", type="csv", key="upload_inflows"
    )
    uploaded_outflows = st.file_uploader(
        "Upload commitments.csv", type="csv", key="upload_outflows"
    )

    if st.button("Load uploaded CSV files"):
        try:
            if uploaded_funds is not None:
                st.session_state.funds = pd.read_csv(
                    uploaded_funds
                ).to_dict(orient="records")
            if uploaded_inflows is not None:
                st.session_state.inflows = pd.read_csv(
                    uploaded_inflows
                ).to_dict(orient="records")
            if uploaded_outflows is not None:
                st.session_state.outflows = pd.read_csv(
                    uploaded_outflows
                ).to_dict(orient="records")
            st.success("Uploaded data loaded for this session.")
        except Exception as exc:
            st.error(f"Could not load uploaded data: {exc}")

    export_forecast = forecast(
        st.session_state.funds,
        st.session_state.inflows,
        st.session_state.outflows,
        months=12,
    )
    st.download_button(
        "Export forecast CSV",
        data=export_forecast.to_csv(index=False),
        file_name="fundbridge_forecast.csv",
        mime="text/csv",
    )

    st.caption(
        "This version stores data only in the active Streamlit session. "
        "It does not provide durable multi-user storage or authentication."
    )
