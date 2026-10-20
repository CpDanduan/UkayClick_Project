"""Render Dashboard interface."""
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from models.inventory import InventoryManager
from models.analytics import BusinessAnalyzer
from repositories.json_repository import load_transactions, load_expenses
from ukayclick_ui import money
from views.common import _parse_record_date

def render_dashboard():
    inv_mgr = InventoryManager()
    analyzer = BusinessAnalyzer()
    inv = analyzer.inventory_summary(inv_mgr.get_products())
    transactions = load_transactions()
    expenses = load_expenses()

    # The dashboard date range defaults to the last seven days, ending today.
    if "dashboard_from_date" not in st.session_state:
        st.session_state.dashboard_from_date = date.today() - timedelta(days=6)
    if "dashboard_to_date" not in st.session_state:
        st.session_state.dashboard_to_date = date.today()

    from_date = st.session_state.dashboard_from_date
    to_date = st.session_state.dashboard_to_date
    dates_reversed = from_date > to_date
    if dates_reversed:
        from_date, to_date = to_date, from_date

    def sales_on_day(day):
        return sum(
            float(t.get("total", 0) or 0)
            for t in transactions
            if _parse_record_date(t) == day
        )

    def sales_between(start_date, end_date):
        return sum(
            float(t.get("total", 0) or 0)
            for t in transactions
            if (record_date := _parse_record_date(t)) is not None
            and start_date <= record_date <= end_date
        )

    def expenses_through(day):
        return sum(
            float(e.get("amount", 0) or 0)
            for e in expenses
            if (record_date := _parse_record_date(e)) is not None
            and record_date <= day
        )

    st.title("Dashboard")
    st.caption(f"Welcome back, {st.session_state.user.get_username()}.")

    # Dashboard metrics use the selected date range (or its end date where noted).
    range_sales = sales_between(from_date, to_date)
    total_sales_through_date = sales_between(date.min, to_date)
    expenses_through_date = expenses_through(to_date)
    week_start = to_date - timedelta(days=to_date.weekday())
    month_start = to_date.replace(day=1)
    weekly_sales = sales_between(week_start, to_date)
    monthly_sales = sales_between(month_start, to_date)
    range_days = max((to_date - from_date).days + 1, 1)
    average_daily_sales = range_sales / range_days
    range_transactions = [
        t for t in transactions
        if (record_date := _parse_record_date(t)) is not None
        and from_date <= record_date <= to_date
    ]
    range_average_sale = (
        sum(float(t.get("total", 0) or 0) for t in range_transactions)
        / len(range_transactions)
        if range_transactions else 0.0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sales in Selected Range", money(range_sales))
    c2.metric("Total Sales to Date", money(total_sales_through_date))
    c3.metric("Expenses to Date", money(expenses_through_date))
    c4.metric("Items in Stock", inv["total_quantity"])

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Average Daily Sales", money(average_daily_sales),
              help="Sales within the selected date range divided by the number of calendar days in that range.")
    d2.metric("Weekly Sales", money(weekly_sales),
              help="Sales from Monday through the selected To date.")
    d3.metric("Monthly Sales", money(monthly_sales),
              help="Sales from the first day of the To date's month through the To date.")
    d4.metric("Net Income to Date", money(total_sales_through_date - expenses_through_date))

    st.divider()

    # Financial, inventory, and product performance summaries share one row.
    overview_col, inventory_col, products_col = st.columns([1, 1, 1])
    with overview_col:
        st.subheader("Financial Overview")
        st.write(f"**Net cash flow to date:** {money(total_sales_through_date - expenses_through_date)}")
        st.write(f"**Transactions in selected range:** {len(range_transactions)}")
        st.write(f"**Average sale in selected range:** {money(range_average_sale)}")
    with inventory_col:
        st.subheader("Inventory Snapshot")
        st.write(f"**Unique products:** {inv['unique_items']}")
        st.write(f"**Low-stock products:** {inv['low_stock']}")
        st.write(f"**Inventory value:** {money(inv['inventory_value'])}")
    with products_col:
        st.subheader("Product Performance")
        product_quantities = {}
        for transaction in range_transactions:
            product_name = str(transaction.get("product", "Unknown product") or "Unknown product")
            quantity_sold = int(transaction.get("quantity", 0) or 0)
            product_quantities[product_name] = product_quantities.get(product_name, 0) + quantity_sold
        if product_quantities:
            best_product = max(product_quantities, key=product_quantities.get)
            least_product = min(product_quantities, key=product_quantities.get)
            st.write("**Best-selling product**")
            st.write(f"{best_product} — {product_quantities[best_product]} sold")
            st.write("**Least-selling product**")
            st.write(f"{least_product} — {product_quantities[least_product]} sold")
        else:
            st.write("**Best-selling product**")
            st.caption("No sales in this date range.")
            st.write("**Least-selling product**")
            st.caption("No sales in this date range.")

    st.divider()

    # Add a visible gap between the sales chart and the bordered date-filter panel.
    chart_col, gap_col, calendar_col = st.columns([2.1, 0.18, 1])
    with chart_col:
        st.subheader("Sales Overview")
        import pandas as pd
        chart_rows = []
        current_day = from_date
        while current_day <= to_date:
            chart_rows.append({"Date": current_day.isoformat(), "Sales": sales_on_day(current_day)})
            current_day += timedelta(days=1)
        chart_df = pd.DataFrame(chart_rows)
        if not chart_df.empty:
            st.bar_chart(chart_df, x="Date", y="Sales", use_container_width=True)
        st.caption(f"Daily sales from {from_date.strftime('%b %d, %Y')} to {to_date.strftime('%b %d, %Y')}.")

    with gap_col:
        st.write("")

    with calendar_col:
        # Offset the panel below the Sales Overview heading so it aligns with the chart area.
        st.write("")
        with st.container(border=True):
            st.subheader("Date Filter")
            st.date_input(
                "From date",
                value=st.session_state.dashboard_from_date,
                key="dashboard_from_date",
                format="YYYY-MM-DD",
            )
            st.date_input(
                "To date",
                value=st.session_state.dashboard_to_date,
                key="dashboard_to_date",
                format="YYYY-MM-DD",
            )
            if st.session_state.dashboard_from_date > st.session_state.dashboard_to_date:
                st.warning("From date must be on or before To date. Please adjust the dates.")

    st.divider()

    # Recent transactions are independent of the dashboard date filter.
    st.subheader("Recent Transactions")
    st.caption("Showing the 10 most recent transactions, regardless of the selected date range.")
    recent_transactions = sorted(
        transactions,
        key=lambda transaction: transaction.get("timestamp", ""),
        reverse=True,
    )[:10]

    if recent_transactions:
        recent_table = [
            {
                "Transaction ID": transaction.get("transaction_id", ""),
                "Date & Time": transaction.get("timestamp", ""),
                "Product": transaction.get("product", ""),
                "Quantity": transaction.get("quantity", 0),
                "Total": money(transaction.get("total", 0)),
                "Payment": transaction.get("payment", ""),
            }
            for transaction in recent_transactions
        ]
        st.dataframe(recent_table, use_container_width=True, hide_index=True)
    else:
        st.info("No sales recorded yet.")

