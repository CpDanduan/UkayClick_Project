"""Render Reports interface."""
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from models.inventory import InventoryManager
from models.analytics import BusinessAnalyzer
from repositories.json_repository import load_transactions, load_expenses
from ukayclick_ui import money
from views.common import _parse_record_date

def render_reports():
    st.title("Reports & Product Analysis")
    st.caption("Review store performance for a selected period and use the results to guide business decisions.")

    all_transactions = load_transactions()
    all_expenses = load_expenses()
    today = date.today()
    default_start = today.replace(day=1)

    # Use the same full-width content grid as the report metric cards below.
    with st.container():
        st.subheader("Report period")
        date_col1, date_col2, group_col = st.columns([1, 1, 1])
        with date_col1:
            report_start = st.date_input("Start date", value=default_start, key="report_start")
        with date_col2:
            report_end = st.date_input("End date", value=today, key="report_end")
        with group_col:
            grouping = st.selectbox("Sales chart grouping", ["Daily", "Weekly", "Monthly"], index=0)

    st.markdown("<div style='height: 0.65rem;'></div>", unsafe_allow_html=True)

    if report_start > report_end:
        st.error("The report start date must be on or before the end date.")
        return

    report_sales = [t for t in all_transactions if _parse_record_date(t) and report_start <= _parse_record_date(t) <= report_end]
    report_expenses = [e for e in all_expenses if _parse_record_date(e) and report_start <= _parse_record_date(e) <= report_end]
    revenue = sum(float(t.get("total", 0) or 0) for t in report_sales)
    expense_total = sum(float(e.get("amount", 0) or 0) for e in report_expenses)
    net = revenue - expense_total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales Revenue", money(revenue))
    c2.metric("Expenses", money(expense_total))
    c3.metric("Net Cash Flow", money(net))
    c4.metric("Transactions", len(report_sales))
    st.caption(f"Report covers {report_start.strftime('%b %d, %Y')} to {report_end.strftime('%b %d, %Y')}.")

    st.subheader("Sales over time")
    if report_sales:
        import pandas as pd
        chart_rows = []
        for transaction in report_sales:
            record_date = _parse_record_date(transaction)
            if grouping == "Weekly":
                label = (record_date - timedelta(days=record_date.weekday())).isoformat()
            elif grouping == "Monthly":
                label = record_date.strftime("%Y-%m")
            else:
                label = record_date.isoformat()
            chart_rows.append({"Period": label, "Sales": float(transaction.get("total", 0) or 0)})
        chart_df = pd.DataFrame(chart_rows).groupby("Period", as_index=False)["Sales"].sum().sort_values("Period")
        st.bar_chart(chart_df, x="Period", y="Sales", use_container_width=True)
    else:
        st.info("No sales were recorded during the selected period.")

    sales_tab, expense_tab = st.tabs(["Sales in Period", "Expenses in Period"])
    with sales_tab:
        if report_sales:
            st.dataframe([{
                "Transaction ID": t.get("transaction_id", ""),
                "Date & Time": t.get("timestamp", ""),
                "Product": t.get("product", ""),
                "Quantity": t.get("quantity", 0),
                "Payment": t.get("payment", ""),
                "Total": money(t.get("total", 0)),
            } for t in sorted(report_sales, key=lambda item: item.get("timestamp", ""), reverse=True)], use_container_width=True, hide_index=True)
        else:
            st.info("No sales to display for this period.")
    with expense_tab:
        if report_expenses:
            st.dataframe([{
                "Expense ID": e.get("expense_id", ""),
                "Date & Time": e.get("timestamp", ""),
                "Category": e.get("category", ""),
                "Description": e.get("description", ""),
                "Amount": money(e.get("amount", 0)),
            } for e in sorted(report_expenses, key=lambda item: item.get("timestamp", ""), reverse=True)], use_container_width=True, hide_index=True)
        else:
            st.info("No expenses to display for this period.")

    st.divider()
    st.subheader("Product Demand Analysis")
    st.caption("Prototype estimate based on all recorded historical units sold, not a machine-learning forecast.")
    mgr = InventoryManager()
    analyzer = BusinessAnalyzer()
    forecast = analyzer.analyze_demand(mgr.get_products())
    if forecast:
        forecast = sorted(forecast, key=lambda item: int(item.get("Units Sold", 0) or 0), reverse=True)
        ranked_forecast = [
            {"Rank": rank, **item}
            for rank, item in enumerate(forecast, start=1)
        ]
        st.dataframe(ranked_forecast, use_container_width=True, hide_index=True)
    else:
        st.info("Add inventory and record sales to estimate product demand.")

    st.subheader("Products Sold")
    product_sales = analyzer.get_product_sales_summary()
    if product_sales:
        st.bar_chart(product_sales, x="Product", y="Units Sold", use_container_width=True)
        best_seller = product_sales[0]
        least_sold = product_sales[-1]
        b1, b2 = st.columns(2)
        b1.metric("Best-Selling Product", best_seller["Product"], f'{best_seller["Units Sold"]} unit(s) sold')
        b2.metric("Least-Sold Product", least_sold["Product"], f'{least_sold["Units Sold"]} unit(s) sold')
    else:
        st.info("Record some sales first to display the product sales chart.")

