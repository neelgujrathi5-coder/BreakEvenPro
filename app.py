import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(page_title="BreakEven Pro", page_icon="📊", layout="wide")

st.markdown("""
<style>
.stApp {background:#0b1020;color:#f8fafc;}
section[data-testid="stSidebar"] {background:#111827;}
div[data-testid="stMetric"] {background:#17263d;border:1px solid #334155;padding:18px;border-radius:14px;}
div[data-testid="stMetric"] label, div[data-testid="stMetric"] [data-testid="stMetricValue"] {color:#f8fafc !important;}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {color:#86efac !important;}
</style>
""", unsafe_allow_html=True)

st.title("📊 BreakEven Pro")
st.caption("Business Break-Even Simulator for small manufacturing start-ups")

st.sidebar.header("Business details")
business = st.sidebar.text_input("Business / product name", "Automotive Metal Components")
currency = st.sidebar.selectbox("Currency", ["₹ INR", "$ USD", "€ EUR", "£ GBP"])
symbol = currency.split()[0]

st.sidebar.header("Monthly manufacturing costs")
st.sidebar.caption("Enter the monthly fixed expenses and the cost to make one unit.")

fixed_rent = st.sidebar.number_input("Factory rent", min_value=0.0, value=15000.0, step=1000.0)
fixed_salary = st.sidebar.number_input("Fixed staff salaries", min_value=0.0, value=20000.0, step=1000.0)
fixed_maintenance = st.sidebar.number_input("Machine maintenance", min_value=0.0, value=5000.0, step=500.0)
fixed_other = st.sidebar.number_input("Other fixed expenses", min_value=0.0, value=10000.0, step=500.0)
fixed_cost = fixed_rent + fixed_salary + fixed_maintenance + fixed_other

st.sidebar.subheader("Variable cost per unit")
raw_material = st.sidebar.number_input("Raw material per unit", min_value=0.0, value=180.0, step=10.0)
labour = st.sidebar.number_input("Direct labour per unit", min_value=0.0, value=60.0, step=5.0)
power = st.sidebar.number_input("Power / electricity per unit", min_value=0.0, value=25.0, step=5.0)
packaging = st.sidebar.number_input("Packaging / other per unit", min_value=0.0, value=35.0, step=5.0)
variable_cost = raw_material + labour + power + packaging

st.sidebar.header("Sales assumptions")
selling_price = st.sidebar.number_input("Selling price per unit", min_value=0.01, value=500.0, step=10.0)
sales_units = st.sidebar.number_input("Expected monthly sales (units)", min_value=0, value=400, step=10)
target_profit = st.sidebar.number_input("Target monthly profit", min_value=0.0, value=30000.0, step=1000.0)
initial_investment = st.sidebar.number_input("Initial investment (optional)", min_value=0.0, value=300000.0, step=10000.0)

contribution = selling_price - variable_cost
if contribution > 0:
    bep = math.ceil(fixed_cost / contribution)
    target_units = math.ceil((fixed_cost + target_profit) / contribution)
else:
    bep = None
    target_units = None

revenue = selling_price * sales_units
total_variable = variable_cost * sales_units
total_cost = fixed_cost + total_variable
profit = revenue - total_cost
margin = (contribution / selling_price * 100) if selling_price > 0 else 0
payback = (initial_investment / profit) if profit > 0 and initial_investment > 0 else None

st.header("Your business snapshot")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Contribution / unit", f"{symbol}{contribution:,.2f}")
c2.metric("Break-even quantity", f"{bep:,} units" if bep is not None else "Not possible")
c3.metric("Monthly profit / loss", f"{symbol}{profit:,.2f}", "Profit" if profit >= 0 else "Loss")
c4.metric("Contribution margin", f"{margin:.1f}%")

if contribution <= 0:
    st.error("Your selling price must be higher than variable cost per unit to make a contribution.")
elif sales_units >= bep:
    st.success(f"{business} must sell at least {bep:,} units per month to cover its fixed and variable costs.")
else:
    st.warning(f"{business} is below break-even. It needs {bep-sales_units:,} more sales units per month to cover costs.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Analysis", "🧾 Cost breakdown", "🧮 Calculations", "📤 Export report", "🧪 What-if analysis"])

with tab1:
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Monthly business result")
        st.metric("Expected monthly revenue", f"{symbol}{revenue:,.2f}")
        st.metric("Expected monthly total cost", f"{symbol}{total_cost:,.2f}")
        st.metric("Expected monthly profit / loss", f"{symbol}{profit:,.2f}")
        st.metric("Units needed for target profit", f"{target_units:,}" if target_units is not None else "Not possible")
        if payback is not None:
            st.metric("Estimated investment recovery", f"{payback:.1f} months")
        elif initial_investment > 0:
            st.info("Investment recovery is not available while monthly profit is zero or negative.")
    with right:
        st.subheader("Revenue vs total cost")
        if contribution > 0:
            max_units = max(sales_units, bep or 0, target_units or 0, 100) * 1.2
            x = list(range(0, int(max_units) + 1, max(1, int(max_units)//30)))
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=[selling_price*n for n in x], mode="lines", name="Revenue"))
            fig.add_trace(go.Scatter(x=x, y=[fixed_cost + variable_cost*n for n in x], mode="lines", name="Total cost"))
            fig.add_vline(x=bep, line_dash="dash", annotation_text=f"Break-even: {bep} units")
            fig.update_layout(template="plotly_dark", xaxis_title="Units sold per month", yaxis_title=f"Amount ({currency})", margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("A break-even chart requires selling price to be higher than variable cost per unit.")

with tab2:
    st.subheader("Monthly fixed cost breakdown")
    fixed_df = pd.DataFrame([
        ["Factory rent", fixed_rent], ["Fixed staff salaries", fixed_salary],
        ["Machine maintenance", fixed_maintenance], ["Other fixed expenses", fixed_other]
    ], columns=["Fixed cost category", "Monthly amount"])
    st.dataframe(fixed_df.assign(**{"Monthly amount": fixed_df["Monthly amount"].map(lambda v: f"{symbol}{v:,.2f}")}), use_container_width=True, hide_index=True)
    st.metric("Total monthly fixed cost", f"{symbol}{fixed_cost:,.2f}")
    st.divider()
    st.subheader("Variable manufacturing cost per unit")
    variable_df = pd.DataFrame([
        ["Raw material", raw_material], ["Direct labour", labour],
        ["Power / electricity", power], ["Packaging / other", packaging]
    ], columns=["Variable cost category", "Cost per unit"])
    st.dataframe(variable_df.assign(**{"Cost per unit": variable_df["Cost per unit"].map(lambda v: f"{symbol}{v:,.2f}")}), use_container_width=True, hide_index=True)
    st.metric("Total variable cost per unit", f"{symbol}{variable_cost:,.2f}")
    st.caption("Tip: Use actual monthly bills, salary amounts and supplier quotations for realistic estimates.")

with tab3:
    st.subheader("Calculation details")
    st.write(f"**Contribution per unit** = Selling price − Variable cost = {symbol}{selling_price:,.2f} − {symbol}{variable_cost:,.2f} = **{symbol}{contribution:,.2f}**")
    st.write(f"**Total fixed cost** = {symbol}{fixed_cost:,.2f}")
    if bep is not None:
        st.write(f"**Break-even quantity** = Fixed cost ÷ Contribution per unit = {fixed_cost:,.2f} ÷ {contribution:,.2f} = **{bep:,} units** (rounded up)")
        st.write(f"**Target-profit quantity** = (Fixed cost + Target profit) ÷ Contribution = **{target_units:,} units**")
    st.write(f"**Monthly profit / loss** = Revenue − Total cost = {symbol}{revenue:,.2f} − {symbol}{total_cost:,.2f} = **{symbol}{profit:,.2f}**")

with tab4:
    st.subheader("Download your business report")
    report_rows = [
        ["Business / product", business],
        ["Monthly fixed cost", fixed_cost],
        ["Variable cost per unit", variable_cost],
        ["Selling price per unit", selling_price],
        ["Expected monthly sales", sales_units],
        ["Break-even quantity", bep if bep is not None else "Not possible"],
        ["Monthly revenue", revenue],
        ["Monthly total cost", total_cost],
        ["Monthly profit / loss", profit],
        ["Units for target profit", target_units if target_units is not None else "Not possible"],
        ["Initial investment", initial_investment],
        ["Estimated payback months", round(payback, 2) if payback is not None else "Not available"]
    ]
    report_df = pd.DataFrame(report_rows, columns=["Metric", "Value"])
    st.download_button("Download report as CSV", report_df.to_csv(index=False).encode("utf-8"), file_name="BreakEvenPro_Report.csv", mime="text/csv")
    st.download_button("Download fixed cost breakdown", fixed_df.to_csv(index=False).encode("utf-8"), file_name="Fixed_Cost_Breakdown.csv", mime="text/csv")
    st.download_button("Download variable cost breakdown", variable_df.to_csv(index=False).encode("utf-8"), file_name="Variable_Cost_Breakdown.csv", mime="text/csv")

    # Generate a clean PDF business report in memory.
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = [Paragraph("BreakEven Pro – Manufacturing Business Report", styles["Title"]), Spacer(1, 10),
             Paragraph(f"Business / product: {business}", styles["Normal"]),
             Paragraph("Educational estimate based on the inputs entered in the simulator.", styles["Normal"]), Spacer(1, 14)]
    pdf_rows = [["Metric", "Value"],
        ["Monthly fixed cost", f"{symbol}{fixed_cost:,.2f}"],
        ["Variable cost per unit", f"{symbol}{variable_cost:,.2f}"],
        ["Selling price per unit", f"{symbol}{selling_price:,.2f}"],
        ["Expected monthly sales", f"{sales_units:,} units"],
        ["Break-even quantity", f"{bep:,} units" if bep is not None else "Not possible"],
        ["Monthly revenue", f"{symbol}{revenue:,.2f}"],
        ["Monthly total cost", f"{symbol}{total_cost:,.2f}"],
        ["Monthly profit / loss", f"{symbol}{profit:,.2f}"],
        ["Target-profit quantity", f"{target_units:,} units" if target_units is not None else "Not possible"],
        ["Initial investment", f"{symbol}{initial_investment:,.2f}"],
        ["Estimated payback", f"{payback:.1f} months" if payback is not None else "Not available"]]
    tbl = Table(pdf_rows, colWidths=[245, 245])
    tbl.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f3b5b")),
                             ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                             ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
                             ("PADDING", (0,0), (-1,-1), 8)]))
    story.extend([tbl, Spacer(1, 14), Paragraph("Formula: Break-even units = Monthly fixed cost ÷ (Selling price − Variable cost per unit), rounded up.", styles["BodyText"]), Spacer(1, 8), Paragraph("This report is for educational planning only and is not financial advice.", styles["Italic"])])
    doc.build(story)
    st.download_button("📄 Download professional PDF report", pdf_buffer.getvalue(), file_name="BreakEvenPro_Business_Report.pdf", mime="application/pdf")

with tab5:
    st.subheader("What-if analysis")
    st.caption("Change the assumptions below to see how your break-even point and profit could change. These sliders do not change your main inputs.")
    w1, w2 = st.columns(2)
    with w1:
        price_change = st.slider("Selling price change (%)", min_value=-30, max_value=30, value=0, step=5)
        material_change = st.slider("Raw material cost change (%)", min_value=-30, max_value=50, value=0, step=5)
    with w2:
        sales_change = st.slider("Monthly sales change (%)", min_value=-50, max_value=100, value=0, step=5)
        fixed_change = st.slider("Fixed cost change (%)", min_value=-30, max_value=50, value=0, step=5)
    what_price = selling_price * (1 + price_change / 100)
    what_variable = variable_cost + raw_material * material_change / 100
    what_fixed = fixed_cost * (1 + fixed_change / 100)
    what_sales = max(0, round(sales_units * (1 + sales_change / 100)))
    what_contribution = what_price - what_variable
    what_revenue = what_price * what_sales
    what_profit = what_revenue - what_fixed - what_variable * what_sales
    what_bep = math.ceil(what_fixed / what_contribution) if what_contribution > 0 else None
    q1, q2, q3 = st.columns(3)
    q1.metric("Scenario break-even", f"{what_bep:,} units" if what_bep is not None else "Not possible")
    q2.metric("Scenario monthly profit / loss", f"{symbol}{what_profit:,.2f}", delta=f"{what_profit-profit:,.2f} vs current")
    q3.metric("Scenario sales", f"{what_sales:,} units")
    st.write(f"Scenario selling price: **{symbol}{what_price:,.2f}** · Scenario variable cost: **{symbol}{what_variable:,.2f}** · Scenario fixed cost: **{symbol}{what_fixed:,.2f}**")
    if what_contribution <= 0:
        st.warning("In this scenario, selling price does not cover variable cost per unit.")
    elif what_bep is not None and what_sales < what_bep:
        st.warning(f"This scenario is below break-even by {what_bep-what_sales:,} units.")
    else:
        st.success("This scenario reaches or exceeds break-even.")

st.caption("BreakEven Pro is an educational planning tool. Use verified business data before making financial decisions.")
