import streamlit as st
import numpy as np
import pandas as pd
from pyxirr import xirr # Import xirr
from pyxirr import mirr # Import mirr

st.set_page_config(page_title="Battery Storage NPV Model", layout="wide")

st.html(
    """
    <details>
        <summary style="cursor: pointer; font-weight: bold; color: #2a9df4;">Click to view/hide Tool Explanation & Instructions</summary>
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-top: 10px;">
        <h2 style="color: #2a9df4;">🔋 Battery Storage Project NPV & Cash Flow Analyzer</h2>
        <p>This tool helps analyze the financial viability of a battery storage project from both the customer's and EQORE's perspective.
        It calculates Net Present Value (NPV), Internal Rate of Return (IRR), Modified Internal Rate of Return (MIRR), and Discounted Payback Period.</p>

        <h4>How to Use:</h4>
        <ul style="padding-left: 20px;>
            <li><b>Load an Example (Optional):</b> Click "Thermofusion Example" or "Aalberts Example" in the sidebar to pre-fill inputs with sample data.</li>
            <li><b>Adjust Inputs:</b> Modify the parameters in the sidebar sections:
                <ul style="padding-left: 20px;">
                    <li><b>Project & Savings section:</b> Define the core project characteristics and electricity savings.</li>
                    <li><b>Tax & Depreciation section:</b> Set corporate tax rates, IRA tax credits, and depreciation schedules.</li>
                    <li><b>Financing section:</b> Specify loan terms if the project is financed.</li>
                </ul>
            </li>
            <li><b>Review Outputs:</b> The main panel will display:
                <ul style="padding-left: 20px;">
                    <li><b>Key Outputs:</b> NPVs for different components, overall project NPV, customer NPV, IRR, MIRR, and payback period.</li>
                    <li><b>Annual Cash Flows Table:</b> A detailed year-by-year breakdown of cash flows for the customer, EQORE, and the total project.</li>
                    <li><b>Charts:</b> Visualizations of EQORE's and the customer's cash flows over the project life.</li>
                </ul>
            </li>
        </ul>

        <h4>Sidebar Input Sections:</h4>
        <ul style="padding-left: 20px;">
            <li><strong>Examples:</strong> Quick-load predefined scenarios.</li>
            <li><strong>Project & Savings:</strong>
                <ul style="padding-left: 20px;">
                    <li><b>Upfront Investment ($):</b> Total initial cost of the battery system.</li>
                    <li><b>Discount Rate (%):</b> Annual rate used to discount future cash flows to their present value. Reflects the time value of money and risk.</li>
                    <li><b>Project Life (years):</b> Expected operational lifetime of the battery system.</li>
                    <li><b>Year-1 Electricity Savings ($):</b> Estimated electricity bill savings in the first year of operation.</li>
                    <li><b>Savings Escalation Rate (%):</b> Annual rate at which electricity savings are expected to increase (e.g., due to rising utility prices).</li>
                    <li><b>EQORE Savings Share (%):</b> The percentage of total gross electricity savings allocated to EQORE. The remainder goes to the customer.</li>
                </ul>
            </li>
            <li><strong>Tax & Depreciation:</strong>
                <ul style="padding-left: 20px;">
                    <li><b>Federal Corp Tax Rate (%):</b> Corporate income tax rate applicable to the customer.</li>
                    <li><b>IRA Tax Credit (%):</b> Percentage of the investment eligible for an Investment Tax Credit under the Inflation Reduction Act.</li>
                    <li><b>Bonus Depreciation (%):</b> Percentage of the investment that can be depreciated immediately in Year 0.</li>
                    <li><em>MACRS rates are pre-defined for a 5-year schedule.</em></li>
                </ul>
            </li>
            <li><strong>Financing:</strong>
                <ul style="padding-left: 20px;">
                    <li><b>Percent Financed (%):</b> Portion of the upfront investment covered by a loan.</li>
                    <li><b>Loan Interest Rate (%):</b> Annual interest rate on the loan.</li>
                    <li><b>Loan Term (years):</b> Duration over which the loan will be repaid.</li>
                </ul>
            </li>
        </ul>

        <h4>Main Panel Outputs:</h4>
        <ul style="padding-left: 20px;">
            <li><strong>Key Outputs:</strong> Summarizes the main financial metrics.
                <ul style="padding-left: 20px;">
                    <li><b>NPV of ... Savings/Shields:</b> Present value of various cash flow streams like gross savings, tax shields from depreciation and interest.</li>
                    <li><b>IRA Tax Credit & Loan Principal:</b> Values received by the customer at the start (t=0).</li>
                    <li><b>Down Payment / Equity:</b> Customer's initial cash outlay.</li>
                    <li><b>EQORE's Net NPV:</b> Net present value of cash flows to EQORE.</li>
                    <li><b>Customer's Net NPV:</b> Net present value of cash flows to the customer. A positive NPV generally indicates a financially attractive project for the customer.</li>
                    <li><b>Customer's IRR:</b> Internal Rate of Return for the customer. The discount rate at which the NPV of customer cash flows is zero. Higher is generally better.</li>
                    <li><b>Customer's MIRR:</b> Modified Internal Rate of Return. Adjusts IRR by assuming reinvestment at a specified rate (here, the discount rate), often considered more realistic than IRR.</li>
                    <li><b>Discounted Payback Period (Customer):</b> The time it takes for the cumulative discounted cash flows for the customer to equal or exceed the initial investment.</li>
                    <li><b>Total Project Net NPV:</b> Combined NPV for EQORE and the customer.</li>
                </ul>
            </li>
            <li><strong>Annual Cash Flows Table:</strong> Provides a detailed yearly breakdown of all financial components.
                <ul style="padding-left: 20px; list-style-type: disc;"> 
                    <li><b>Year:</b> Project year, with Year 0 representing the initial investment point.</li>
                    <li><b>Total Gross Savings:</b> Total electricity savings generated by the battery system before any splits or deductions.</li>
                    <li><b>EQORE Savings (CF):</b> The portion of gross electricity savings allocated to EQORE as cash flow.</li>
                    <li><b>Customer Gross Savings:</b> The portion of gross electricity savings allocated to the customer before their specific costs/taxes.</li>
                    <li><b>Depreciation:</b> Annual non-cash expense recognized for the wear and tear of the asset, used for tax calculations.</li>
                    <li><b>Depr. Tax Shield:</b> The amount of tax saved due to the depreciation expense (Calculated as Depreciation * Corporate Tax Rate).</li>
                    <li><b>Interest Paid:</b> The interest component of any loan payments made during the year.</li>
                    <li><b>Principal Paid:</b> The principal repayment component of any loan payments made during the year.</li>
                    <li><b>Interest Tax Shield:</b> The amount of tax saved due to the interest expense (Calculated as Interest Paid * Corporate Tax Rate).</li>
                    <li><b>Loan Proceeds/(Repay):</b> Net cash flow related to financing. Positive in Year 0 if a loan is taken (proceeds received), negative in subsequent years for repayments (interest + principal).</li>
                    <li><b>Customer Total CF:</b> The net annual cash flow for the customer after all their specific revenues, costs, tax impacts, and financing flows.</li>
                    <li><b>EQORE Total CF:</b> The net annual cash flow for EQORE (currently this is the same as their savings share, but could include other costs/revenues for EQORE in more complex models).</li>
                    <li><b>Total Project CF:</b> The combined net cash flow of the Customer and EQORE, representing the overall project's cash generation.</li>
                </ul>
            </li>
            <li><strong>Charts:</strong> Visual representation of cash flows over time for EQORE and the customer.</li>
        </ul>
        </div>
    </details>
    <br>
    """
)

st.title("🔋 Battery Storage Project NPV Model")

# ─── Sidebar Inputs ──────────────────────────────────────────────────────────
THERMOFUSION = {
    "investment": 186900.00, "discount_rate": 4.5, "project_life": 15,
    "base_savings": 94000.00, "escalation": 3.0, "corp_tax": 28.0,
    "ira_credit_pct": 30.0, "bonus_depr_pct": 40.0, "finance_pct": 80.0,
    "loan_rate": 9.0, "loan_term": 3, "savings_split": 33.0, # Added savings_split
}
AALBERTS = {
    "investment": 72000.00, "discount_rate": 4.5, "project_life": 15,
    "base_savings": 15600.00, "escalation": 3.0, "corp_tax": 28.0,
    "ira_credit_pct": 30.0, "bonus_depr_pct": 40.0, "finance_pct": 80.0,
    "loan_rate": 9.0, "loan_term": 3, "savings_split": 15.0, # Added savings_split
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
    "Year": years, # Project year, Year 0 is initial investment point
    "Total Gross Savings": total_savings_arr, # Total electricity savings generated by the system
    "EQORE Savings (CF)": eqore_cf, # Portion of gross savings allocated to EQORE
    "Customer Gross Savings": customer_gross_savings, # Portion of gross savings allocated to the customer
    "Depreciation": depreciation_arr, # Annual depreciation expense for tax purposes
    "Depr. Tax Shield": depreciation_tax_shield_arr, # Tax savings due to depreciation (Depreciation * Tax Rate)
    "Interest Paid": interest_payments, # Interest portion of loan payments
    "Principal Paid": principal_payments, # Principal portion of loan payments
    "Interest Tax Shield": interest_tax_shield_arr, # Tax savings due to interest expense (Interest Paid * Tax Rate)
    "Loan Proceeds/(Repay)": financing_cash_flow, # Net cash flow from financing (Loan received - loan repayments)
    "Customer Total CF": customer_cf, # Net annual cash flow for the customer
    "EQORE Total CF": eqore_cf, # Net annual cash flow for EQORE (currently same as their savings share)
    "Total Project CF": total_project_cf, # Combined net cash flow of Customer and EQORE
})

st.subheader("Annual Cash Flows")
st.caption("This table shows the detailed breakdown of cash flows year by year for the project, customer, and EQORE.")
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
    st.caption("This chart displays EQORE's net cash flow over the project life.")
    st.line_chart(cf_df.set_index("Year")[["EQORE Total CF"]]) # Simplified if only one CF item
with col_chart2:
    st.subheader("Customer Cash Flows")
    st.caption("This chart displays the customer's gross savings versus their net total cash flow over the project life.")
    st.line_chart(cf_df.set_index("Year")[["Customer Gross Savings", "Customer Total CF"]])

st.subheader("Project Cash Flow Components (Customer)")
st.caption("This bar chart breaks down the customer's total annual cash flow into its major components: gross savings, depreciation tax shield, interest paid (negative), and principal paid (negative).")
st.bar_chart(cf_df.set_index("Year")[["Customer Gross Savings", "Depr. Tax Shield", "Interest Paid", "Principal Paid", "Customer Total CF"]])

