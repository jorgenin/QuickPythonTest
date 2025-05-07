import streamlit as st
import numpy as np
import pandas as pd
from pyxirr import xirr # Import xirr
from pyxirr import mirr # Import mirr

st.set_page_config(page_title="Battery Storage NPV Model", layout="wide")
st.title("🔋 Battery Storage Project NPV Model")

# ─── Sidebar Inputs ──────────────────────────────────────────────────────────
THERMOFUSION = {
    "investment": 186900.00, "discount_rate": 4.5, "project_life": 15,
    "base_savings": 94000.00, "escalation": 3.0, "corp_tax": 28.0,
    "ira_credit_pct": 30.0, "bonus_depr_pct": 40.0, "finance_pct": 80.0,
    "loan_rate": 9.0, "loan_term": 3, "savings_split": 50.0, # Added savings_split
}
AALBERTS = {
    "investment": 72000.00, "discount_rate": 4.5, "project_life": 15,
    "base_savings": 15600.00, "escalation": 3.0, "corp_tax": 28.0,
    "ira_credit_pct": 30.0, "bonus_depr_pct": 40.0, "finance_pct": 80.0,
    "loan_rate": 9.0, "loan_term": 3, "savings_split": 50.0, # Added savings_split
}

def set_example(values):
    for k, v in values.items():
        st.session_state[k] = v

st.sidebar.header("Examples")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Thermofusion Example"):
        set_example(THERMOFUSION)
with col2:
    if st.button("Aalberts Example"):
        set_example(AALBERTS)

st.sidebar.header("1. Project & Savings")
investment = st.sidebar.number_input(
    "Upfront Investment ($)", value=st.session_state.get("investment", 188_571.50), step=1.0, format="%.2f", key="investment"
)
discount_rate = st.sidebar.number_input(
    "Discount Rate (%)", value=st.session_state.get("discount_rate", 7.0), step=0.1, format="%.2f", key="discount_rate"
) / 100.0
project_life = st.sidebar.slider("Project Life (years)", 1, 30, st.session_state.get("project_life", 20), key="project_life")

base_savings = st.sidebar.number_input(
    "Year-1 Electricity Savings ($)", value=st.session_state.get("base_savings", 28_000.0), format="%.2f", key="base_savings"
)
escalation = st.sidebar.number_input(
    "Savings Escalation Rate (%)", value=st.session_state.get("escalation", 5.9), step=0.1, format="%.2f", key="escalation"
) / 100.0
savings_split = st.sidebar.slider(
    "EQORE Savings Share (%)", min_value=0.0, max_value=100.0, value=st.session_state.get("savings_split", 50.0), step=5.0, key="savings_split"
) / 100.0

st.sidebar.header("2. Tax & Depreciation")
corp_tax = st.sidebar.number_input(
    "Federal Corp Tax Rate (%)", value=st.session_state.get("corp_tax", 21.0), step=0.1, format="%.2f", key="corp_tax"
) / 100.0
ira_credit_pct = st.sidebar.number_input(
    "IRA Tax Credit (%)", value=st.session_state.get("ira_credit_pct", 30.0), step=1.0, format="%.2f", key="ira_credit_pct"
) / 100.0
bonus_depr_pct = st.sidebar.number_input(
    "Bonus Depreciation (%)", value=st.session_state.get("bonus_depr_pct", 100.0), step=5.0, format="%.2f", key="bonus_depr_pct"
) / 100.0
macrs_rates = np.array([0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576]) # 5-yr MACRS

st.sidebar.header("3. Financing")
finance_pct = st.sidebar.number_input(
    "Percent Financed (%)", value=st.session_state.get("finance_pct", 80.0), step=1.0, format="%.2f", key="finance_pct"
) / 100.0
loan_rate = st.sidebar.number_input(
    "Loan Interest Rate (%)", value=st.session_state.get("loan_rate", 5.0), step=0.1, format="%.2f", key="loan_rate"
) / 100.0
loan_term = st.sidebar.slider("Loan Term (years)", 1, project_life, st.session_state.get("loan_term", 5), key="loan_term")

# ─── Build Year Index & Discount Factors ────────────────────────────────────
years = np.arange(0, project_life + 1)
dfac = 1 / (1 + discount_rate) ** years

# ─── 1) Savings Profile ───────────────────────────────────────────────
total_savings_arr = np.zeros_like(years, float) # Renamed for clarity
total_savings_arr[1:] = base_savings * (1 + escalation) ** (years[1:] - 1)

eqore_savings = total_savings_arr * savings_split
customer_gross_savings = total_savings_arr * (1 - savings_split) # Customer's share of gross savings

# ─── 2) IRA Credit at t=0 ───────────────────────────────────────────────────
ira_credit = ira_credit_pct * investment

# ─── 3) Depreciation Schedule ──────────────────────────────────────────
depreciation_arr = np.zeros_like(years, float)
# Bonus Depreciation in Year 0
depreciation_arr[0] = bonus_depr_pct * investment

# MACRS Depreciation (on remaining basis, starting Year 1)
macrs_basis = investment * (1 - bonus_depr_pct)
for i in range(len(macrs_rates)):
    year_idx = i + 1  # MACRS Year 1 is Project Year 1
    if year_idx < len(depreciation_arr):
        depreciation_arr[year_idx] = macrs_rates[i] * macrs_basis
    else:
        break # Project life is shorter than MACRS schedule

depreciation_tax_shield_arr = depreciation_arr * corp_tax

# ─── 4) Financing Schedule ─────────────────────────────────────────────────
loan_principal_amount = finance_pct * investment
down_payment = investment - loan_principal_amount # Equity from customer

loan_pmt = 0
if loan_principal_amount > 0 and loan_term > 0:
    if loan_rate > 0:
        annuity_factor = (loan_rate * (1 + loan_rate) ** loan_term) / \
                         ((1 + loan_rate) ** loan_term - 1)
        loan_pmt = loan_principal_amount * annuity_factor
    else: # loan_rate is 0
        loan_pmt = loan_principal_amount / loan_term

interest_payments = np.zeros_like(years, float)
principal_payments = np.zeros_like(years, float)
financing_cash_flow = np.zeros_like(years, float) # Net cash flow from debt

financing_cash_flow[0] = loan_principal_amount # Loan received

if loan_principal_amount > 0 and loan_term > 0:
    remaining_balance = loan_principal_amount
    for y_idx in range(1, int(loan_term) + 1):
        if y_idx >= len(years): break
        if remaining_balance <= 1e-2: break # Effectively zero

        current_interest = remaining_balance * loan_rate
        # For zero interest loan, loan_pmt is principal, interest is 0
        current_principal = loan_pmt - current_interest if loan_rate > 0 else loan_pmt
        
        # Adjust last payment to clear remaining balance precisely
        if remaining_balance - current_principal < 1e-2 and remaining_balance - current_principal > -1e-2 : # effectively zero
             current_principal = remaining_balance
        elif remaining_balance < current_principal: # If payment overshoots
            current_principal = remaining_balance
            if loan_rate > 0 : # Recalculate interest if principal adjusted
                 current_interest = loan_pmt - current_principal
            else: # if loan rate is 0, interest is always 0
                 current_interest = 0


        interest_payments[y_idx] = current_interest
        principal_payments[y_idx] = current_principal
        financing_cash_flow[y_idx] = -(current_interest + current_principal) # Total payment outflow
        remaining_balance -= current_principal

interest_tax_shield_arr = interest_payments * corp_tax

# ─── 5) Stakeholder Cash Flows & NPVs ─────────────────────────────────────

# EQORE Cash Flows (assumed to be a simple payout of gross savings share)
eqore_cf = eqore_savings.copy() # Start with their savings share
eqore_npv = (eqore_cf * dfac).sum()
# If EQORE had investment or taxes, they would be here.

# Customer Cash Flows
customer_cf = np.zeros_like(years, float)

# Year 0 for Customer:
# Outflows: Full Investment
# Inflows: IRA Credit, Loan Principal Received
# Tax Impact: Bonus Depreciation Tax Shield
customer_cf[0] = -investment + ira_credit + loan_principal_amount + depreciation_tax_shield_arr[0]

# Years 1+ for Customer:
# Levered Free Cash Flow to Equity approach:
# (Savings - Interest) * (1 - Tax Rate) + Depreciation Tax Shield - Principal Repayments
for y_idx in range(1, project_life + 1):
    customer_cf[y_idx] = (customer_gross_savings[y_idx] - interest_payments[y_idx]) * (1 - corp_tax) \
                       + depreciation_tax_shield_arr[y_idx] \
                       - principal_payments[y_idx]

customer_npv = (customer_cf * dfac).sum()

# Total Project Cash Flows (Sum of Stakeholders)
# This represents the combined cash flow if EQORE and Customer are the only stakeholders.
total_project_cf = eqore_cf + customer_cf
total_project_npv = (total_project_cf * dfac).sum() # Or eqore_npv + customer_npv

# Calculate Customer IRR
start_date = pd.to_datetime("today")
dates = pd.date_range(start_date, periods=project_life + 1, freq="YE") # 'YE' for year-end
dates = dates.to_series().reset_index(drop=True)
dates.iloc[0] = start_date # Year 0 cash flow is today

try:
    customer_irr_val = xirr(dates, customer_cf)
    if customer_irr_val is None:
        customer_irr_display = "N/A (no solution)"
    else:
        customer_irr_display = f"{customer_irr_val*100:.2f}%"
except Exception as e:
    customer_irr_display = f"N/A (error: {e})"

# Calculate MIRR
try:
    # Using discount_rate for both finance and reinvestment rate as a common starting point
    customer_mirr_val = mirr(customer_cf, finance_rate=discount_rate, reinvest_rate=discount_rate, silent=True)
    if customer_mirr_val is None:
        customer_mirr_display = "N/A (no solution)"
    else:
        customer_mirr_display = f"{customer_mirr_val*100:.2f}%"
except Exception as e: # Includes pyxirr.InvalidPaymentsError if not silent and other issues
    customer_mirr_display = f"N/A (error: {e})"

# Calculate Discounted Payback Period
discounted_customer_cf = customer_cf * dfac
cumulative_discounted_cf = np.cumsum(discounted_customer_cf)
payback_period_display = "Never"
# Find first year where cumulative discounted CF turns positive
# We look from year 1 onwards if year 0 is already positive,
# otherwise, we look for the point where the initial negative turns positive.
# If customer_cf[0] is positive, payback is immediate (Year 0) in one sense,
# or we look for when the *project* breaks even on a discounted basis.
# Let's define payback as the first year cumulative discounted CF >= 0

# Ensure we handle the case where customer_cf[0] might be positive.
# If customer_cf[0] >= 0, and it's the only cash flow or all subsequent are also non-negative,
# it could be considered immediate. However, typically payback looks for recovery of an investment.
# Given customer_cf[0] can be positive, a more nuanced check is needed.
# Let's find the first year where cumulative_discounted_cf >= 0
positive_cumulative_indices = np.where(cumulative_discounted_cf >= -1e-9)[0] # Allow for small floating point inaccuracies
if len(positive_cumulative_indices) > 0:
    payback_year = positive_cumulative_indices[0]
    if payback_year == 0:
        if customer_cf[0] >= -1e-9: # If Year 0 CF itself is non-negative
             payback_period_display = "Year 0 (Immediate)"
        else: # This case should not happen if cum_disc_cf[0] >=0 and cf[0] < 0
             payback_period_display = "Year 0" # Fallback, review logic if hit
    else:
        # Interpolate for more precision if needed, for now, just the year
        payback_period_display = f"Year {payback_year}"
        # For more precision:
        # prev_cumulative_cf = cumulative_discounted_cf[payback_year - 1]
        # current_year_cf = discounted_customer_cf[payback_year]
        # if current_year_cf > 0: # Avoid division by zero if cf is zero
        #     fractional_year = abs(prev_cumulative_cf) / current_year_cf
        #     payback_period_display = f"{payback_year - 1 + fractional_year:.2f} Years"


# ─── Display Results ────────────────────────────────────────────────────────
st.subheader("🔑 Key Outputs")

# For display, calculate total NPVs of components if desired
npv_total_savings_gross = (total_savings_arr * dfac).sum()
npv_eqore_share_gross = (eqore_savings * dfac).sum() # Same as eqore_npv if no other CFs for EQORE
npv_customer_share_gross = (customer_gross_savings * dfac).sum()
npv_depreciation_shield = (depreciation_tax_shield_arr * dfac).sum()
npv_interest_shield = (interest_tax_shield_arr * dfac).sum() # For info

st.markdown(
    rf"""
- NPV of Total Gross Electricity Savings: $NPV_{{total\_savings\_gross}} = {npv_total_savings_gross:,.2f}$
- NPV of EQORE's Share of Gross Savings: $NPV_{{eqore\_share\_gross}} = {npv_eqore_share_gross:,.2f}$
- NPV of Customer's Share of Gross Savings: $NPV_{{customer\_share\_gross}} = {npv_customer_share_gross:,.2f}$
- NPV of Total Depreciation Tax Shield (Customer): $NPV_{{depr\_shield}} = {npv_depreciation_shield:,.2f}$
- NPV of Interest Tax Shield (Customer): $NPV_{{int\_shield}} = {npv_interest_shield:,.2f}$
- IRA Tax Credit (Customer, t=0): $Credit = {ira_credit:,.2f}$
- Loan Principal (Customer, t=0): $Loan = {loan_principal_amount:,.2f}$
- Down Payment / Equity (Customer, t=0): $Equity = {down_payment:,.2f}$

---
- **EQORE's Net NPV**: $NPV_{{eqore}} = {eqore_npv:,.2f}$
- **Customer's Net NPV**: $NPV_{{customer}} = {customer_npv:,.2f}$
- **Customer's IRR**: $IRR_{{customer}} = {customer_irr_display}$
- **Customer's MIRR**: $MIRR_{{customer}} = {customer_mirr_display}$
- **Discounted Payback Period (Customer)**: {payback_period_display}
- **Total Project Net NPV (EQORE + Customer)**: $NPV_{{total\_project}} = {total_project_npv:,.2f}$
"""
)

# ─── Annual CF Table & Chart ───────────────────────────────────────────────
cf_df = pd.DataFrame({
    "Year": years,
    "Total Gross Savings": total_savings_arr,
    "EQORE Savings (CF)": eqore_cf, # EQORE's actual cash flow
    "Customer Gross Savings": customer_gross_savings,
    "Depreciation": depreciation_arr,
    "Depr. Tax Shield": depreciation_tax_shield_arr,
    "Interest Paid": interest_payments,
    "Principal Paid": principal_payments,
    "Interest Tax Shield": interest_tax_shield_arr,
    "Loan Proceeds/(Repay)": financing_cash_flow, # Net loan cash flow
    "Customer Total CF": customer_cf,
    "EQORE Total CF": eqore_cf, # Same as EQORE Savings if no other items
    "Total Project CF": total_project_cf,
})

st.subheader("Annual Cash Flows")
st.dataframe(
    cf_df.style.format({
        "Year": "{:.0f}",
        "Total Gross Savings": "${:,.2f}",
        "EQORE Savings (CF)": "${:,.2f}",
        "Customer Gross Savings": "${:,.2f}",
        "Depreciation": "${:,.2f}",
        "Depr. Tax Shield": "${:,.2f}",
        "Interest Paid": "${:,.2f}",
        "Principal Paid": "${:,.2f}",
        "Interest Tax Shield": "${:,.2f}",
        "Loan Proceeds/(Repay)": "${:,.2f}",
        "Customer Total CF": "${:,.2f}",
        "EQORE Total CF": "${:,.2f}",
        "Total Project CF": "${:,.2f}",
    }),
    height=400
)

col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.subheader("EQORE Cash Flows")
    st.line_chart(cf_df.set_index("Year")[["EQORE Total CF"]]) # Simplified if only one CF item
with col_chart2:
    st.subheader("Customer Cash Flows")
    st.line_chart(cf_df.set_index("Year")[["Customer Gross Savings", "Customer Total CF"]])

st.subheader("Project Cash Flow Components (Customer)")
st.bar_chart(cf_df.set_index("Year")[["Customer Gross Savings", "Depr. Tax Shield", "Interest Paid", "Principal Paid", "Customer Total CF"]])

