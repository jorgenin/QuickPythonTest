import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Battery Storage NPV Model", layout="wide")
st.title("🔋 Battery Storage Project NPV Model")

# ─── Sidebar Inputs ──────────────────────────────────────────────────────────

st.sidebar.header("1. Project & Savings")
investment = st.sidebar.number_input(
    "Upfront Investment ($)", value=188_571.50, step=1.0, format="%.2f"
)
discount_rate = st.sidebar.number_input(
    "Discount Rate (%)", value=7.0, step=0.1, format="%.2f"
) / 100.0
project_life = st.sidebar.slider("Project Life (years)", 1, 30, 20)

base_savings = st.sidebar.number_input(
    "Year-1 Electricity Savings ($)", value=28_000.0, format="%.2f"
)
escalation = st.sidebar.number_input(
    "Savings Escalation Rate (%)", value=5.9, step=0.1, format="%.2f"
) / 100.0

st.sidebar.header("2. Tax & Depreciation")
corp_tax = st.sidebar.number_input(
    "Federal Corp Tax Rate (%)", value=21.0, step=0.1, format="%.2f"
) / 100.0
ira_credit_pct = st.sidebar.number_input(
    "IRA Tax Credit (%)", value=30.0, step=1.0, format="%.2f"
) / 100.0
bonus_depr_pct = st.sidebar.number_input(
    "Bonus Depreciation (%)", value=100.0, step=5.0, format="%.2f"
) / 100.0
# Default 5-year MACRS
macrs = np.array([0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576])

st.sidebar.header("3. Financing")
finance_pct = st.sidebar.number_input(
    "Percent Financed (%)", value=80.0, step=1.0, format="%.2f"
) / 100.0
loan_rate = st.sidebar.number_input(
    "Loan Interest Rate (%)", value=5.0, step=0.1, format="%.2f"
) / 100.0
loan_term = st.sidebar.slider("Loan Term (years)", 1, project_life, 5)

# ─── Build Year Index & Discount Factors ────────────────────────────────────

years = np.arange(0, project_life + 1)
dfac = 1 / (1 + discount_rate) ** years

# ─── 1) Savings Profile & NPV ───────────────────────────────────────────────

savings = np.zeros_like(years, float)
savings[1:] = base_savings * (1 + escalation) ** (years[1:] - 1)
npv_savings = (savings * dfac).sum()

# ─── 2) IRA Credit at t=0 ───────────────────────────────────────────────────

ira_credit = ira_credit_pct * investment

# ─── 3) Depreciation & Tax Shield ──────────────────────────────────────────

dep = np.zeros_like(years, float)
dep[0] = bonus_depr_pct * investment
for i in range(1, min(len(macrs), len(dep))):
    dep[i] = macrs[i] * investment

tax_shield = dep * corp_tax
npv_shield = (tax_shield * dfac).sum()

# ─── 4) Financing Schedule ─────────────────────────────────────────────────

loan_principal = finance_pct * investment
down_payment = investment - loan_principal

# annual loan payment via annuity formula
if loan_rate > 0:
    annuity_factor = (
        loan_rate * (1 + loan_rate) ** loan_term
        / ((1 + loan_rate) ** loan_term - 1)
    )
    loan_pmt = loan_principal * annuity_factor
else:
    loan_pmt = loan_principal / loan_term

fin_cf = np.zeros_like(years, float)
fin_cf[0] = +loan_principal - down_payment
fin_cf[1 : loan_term + 1] = -loan_pmt

# ─── 5) Total Cash Flows & NPV ─────────────────────────────────────────────

ops_cf = savings + tax_shield
total_cf = ops_cf + fin_cf
total_cf[0] += -investment + ira_credit + tax_shield[0]  # net t=0

net_npv = (total_cf * dfac).sum()

# ─── Display Results ────────────────────────────────────────────────────────

st.subheader("🔑 Key Outputs")
st.markdown(
    f"""
- NPV of Electricity Savings:  
  $NPV_{{savings}} = {npv_savings:,.2f}$

- NPV of Depreciation Tax Shield:  
  $NPV_{{shield}} = {npv_shield:,.2f}$

- IRA Tax Credit Today:  
  $Credit = {ira_credit:,.2f}$

- Loan Principal Drawn at $t=0$:  
  $Loan = {loan_principal:,.2f}$

- Down Payment at $t=0$:  
  $Equity = {down_payment:,.2f}$

- **Project Net NPV**:  
  $NPV_{{net}} = {net_npv:,.2f}$
"""
)

# ─── Annual CF Table & Chart ───────────────────────────────────────────────

cf_df = pd.DataFrame({
    "Year": years,
    "Savings": savings,
    "Tax Shield": tax_shield,
    "Financing CF": fin_cf,
    "Total CF": total_cf,
})
st.subheader("Annual Cash Flows")
st.dataframe(
    cf_df.style.format({
        "Year": "{:.0f}",
        "Savings": "${:,.2f}",
        "Tax Shield": "${:,.2f}",
        "Financing CF": "${:,.2f}",
        "Total CF": "${:,.2f}",
    }),
    height=350
)
st.line_chart(cf_df.set_index("Year")["Total CF"])
