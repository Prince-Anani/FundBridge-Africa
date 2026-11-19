# FundBridge Africa — MVP

## What problem does it address?
FundBridge explores a specific decision problem for grant- and sponsorship-funded organisations: whether cash that is actually available, or expected to arrive with stated confidence, can safely support dated programme commitments without spending restricted money outside its permitted purpose.

The MVP includes:
- Separate fund balances (no cross-fund pooling in the commitment checker).
- Expected receipts classified as received, committed, or pipeline.
- Confidence-weighted receipts for forecasting.
- Dated expenditure commitments with essential/deferrable/discretionary labels.
- A basic restriction-category check.
- Monthly forecast and funding-delay / funding-haircut stress test.
- CSV import and export.

## Novelty and prior-art position
Do not claim that cash-flow forecasting, restricted-fund accounting, grant tracking, or scenario analysis is new. Publicly visible products and resources already cover substantial parts:
- Nonprofit Finance Fund: https://nff.org/resource/ask-nff/
- Club Metrics: https://club-metrics.co.uk/
- GrantFlow: https://grantflow.tech/
- Solver nonprofit cash-flow forecast: https://www.solverglobal.com/product/template-marketplace/nonprofit-essentials-cash-flow-forecast
- Brixx charity financial planning: https://brixx.com/solutions/charity/
- JFF guide to public-grant spend-down plans: https://www.jff.org/wp-content/uploads/2025/04/Managing-Spend-Down-Plans-for-Public-Grants.pdf

Potential differentiation to validate: a lightweight, fund-by-fund commitment gate for small multi-country programmes that joins receipt confidence, payment timing, purpose restrictions, and action-prioritised commitment decisions. This is a product hypothesis, not a verified patent claim or proof of global novelty.

A defensible novelty study should search Google Patents, WIPO PATENTSCOPE, Espacenet, academic databases, app marketplaces, and vendor documentation; compare claims and workflows; and interview target organisations. This code is an MVP prototype, not a completed novelty or freedom-to-operate opinion.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit, normally http://localhost:8501.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository and upload all project files.
2. Sign in at https://share.streamlit.io/ using GitHub.
3. Choose **Create app**, select the repository, branch, and `app.py`.
4. Deploy. Streamlit will install packages from `requirements.txt`.
5. Test with fictional data before entering real organisational information.

For production, use a managed database, authentication, role-based access, encrypted secrets, audit logs, backups, input validation, and a documented data-retention policy. Do not put bank credentials or sensitive personal data in this prototype.

## Important limitations
- Session-based storage: data may disappear when the session ends or app restarts.
- No bank feeds, payment execution, donor portal, multi-user permissions, or accounting integrations.
- Forecast confidence is a user-entered assumption, not a statistically calibrated probability.
- Forecast aggregates fund balances; the commitment checker is the more conservative fund-specific check.
- The model is monthly and simplified; it does not handle intra-month payment ordering, foreign-exchange exposure, tax, inflation, interest, or all grant/legal restrictions.
- The demo data uses illustrative dates and amounts.
- Obtain qualified accounting and legal review before using the output to approve real spending.

## Data files
- `sample_funds.csv`
- `sample_funding.csv`
- `sample_commitments.csv`

All sample data is fictional.


## Update: DataFrame compatibility fix
The financial engine now normalises Streamlit `st.data_editor` outputs.
`forecast`, `scenario_forecast`, and `commitment_check` accept either Pandas
DataFrames or lists of dictionaries. The dashboard also converts the edited
fund table before calculating opening cash. Regression tests cover DataFrame
inputs to the forecast, stress test, and commitment checker.
