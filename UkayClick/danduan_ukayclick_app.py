import streamlit as st
from datetime import date, datetime, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from ukayclick_auth import Authentication
from ukayclick_inventory import InventoryManager, Product
from ukayclick_sales import process_sale
from ukayclick_expenses import ExpenseManager
from ukayclick_analytics import BusinessAnalyzer
from ukayclick_ereceipt import EReceipt
from ukayclick_ui import apply_style, money
from ukayclick_storage import load_transactions, save_transactions, load_expenses, save_expenses, set_current_user


st.set_page_config(
    page_title="UkayClick",
    layout="wide",
)

apply_style()
auth = Authentication()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None


def _set_success_feedback(message):
    """Keep action confirmation visible after a Streamlit rerun."""
    st.session_state["ukayclick_success_feedback"] = message


def _show_success_feedback():
    """Display and clear the latest one-time success confirmation."""
    message = st.session_state.pop("ukayclick_success_feedback", None)
    if message:
        st.success(message)


def login_screen():
    st.write("")
    st.write("")
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        st.markdown(
            "<div class='ukay-login-brand'><div class='ukay-eyebrow'>THRIFT STORE MANAGEMENT</div><h1>UkayClick</h1><p class='ukay-subtitle'>A simpler way to manage your store.</p></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.subheader("Welcome back")
            st.caption("Log in to continue to your dashboard.")
            tab1, tab2 = st.tabs(["Log In", "Create Account"])

            with tab1:
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                if st.button("Log In", use_container_width=True):
                    user = auth.authenticate(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

            with tab2:
                username = st.text_input("Create Username", key="reg_username")
                password = st.text_input("Create Password", type="password", key="reg_password")
                confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                if st.button("Create Account", use_container_width=True):
                    ok, msg = auth.register(username, password, confirm)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def dashboard():
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

def sales_page():
    st.title("Process Sale")

    inv_mgr = InventoryManager()
    available = [
        product
        for product in inv_mgr.get_products()
        if product.is_available()
    ]

    if not available:
        st.warning("No items are currently available for sale.")
        return

    choices = {
        f"{product.item_id} — {product.name} ({money(product.price)})": product
        for product in available
    }

    selected = st.selectbox("Product", list(choices))
    item = choices[selected]

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        max_value=item.quantity,
        value=1,
    )
    sale_date = st.date_input(
        "Sale Date",
        value=date.today(),
        help="Choose the date this sale should be recorded under.",
        key="process_sale_date",
    )
    customer = st.text_input("Customer name (optional)")
    payment = st.selectbox(
        "Payment Method",
        ["Cash", "GCash", "Other"],
    )

    customer_payment = 0.0
    if payment == "Cash":
        customer_payment = st.number_input(
            "Cash received",
            min_value=0.0,
            step=10.0,
            value=0.0,
        )

    total = item.price * quantity
    st.metric("Total", money(total))

    if payment == "Cash":
        change = max(customer_payment - total, 0)
        st.write(f"**Change:** {money(change)}")

    if st.button("✓ Complete Sale", use_container_width=True):
        ok, result = process_sale(
            inv_mgr,
            item.item_id,
            quantity,
            customer,
            payment,
            customer_payment,
            sale_date=sale_date,
        )

        if ok:
            st.session_state.last_receipt = result
            st.success("Sale recorded and inventory updated.")
            st.rerun()
        else:
            st.error(result)

    if st.session_state.last_receipt:
        st.divider()
        st.subheader("E-Receipt")
        st.code(
            EReceipt(st.session_state.last_receipt).generate(),
            language="text",
        )

        if st.button("Clear Receipt"):
            st.session_state.last_receipt = None
            st.rerun()


def inventory_page():
    _show_success_feedback()
    st.title("Inventory Management")

    mgr = InventoryManager()
    inventory = mgr.get_products()

    with st.expander("Add New Product"):
        with st.form("add_item"):
            name = st.text_input("Product name")
            category = st.selectbox(
                "Category",
                [
                    "Shirt",
                    "Pants",
                    "Dress",
                    "Jacket",
                    "Shoes",
                    "Accessories",
                    "Other",
                ],
            )
            price = st.number_input(
                "Selling price",
                min_value=0.01,
                step=10.0,
            )
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1,
            )
            cost = st.number_input(
                "Acquisition cost per item",
                min_value=0.0,
                step=10.0,
            )

            if st.form_submit_button("Add Product"):
                if not name.strip():
                    st.error("Product name is required.")
                else:
                    product = Product(
                        mgr.next_item_id(),
                        name,
                        category,
                        price,
                        cost,
                        quantity,
                    )
                    mgr.add_product(product)
                    _set_success_feedback(f"Successfully added '{name.strip()}' to inventory.")
                    st.rerun()

    # Keep product maintenance in a matching collapsible section directly below
    # Add New Product, so the inventory page stays compact until needed.
    with st.expander("Update / Remove Product"):
        if not inventory:
            st.info("Add a product first to update or remove inventory.")
        else:
            ids = [product.item_id for product in inventory]
            item_id = st.selectbox("Select Item ID", ids, key="inventory_manage_item_id")
            item = mgr.find_product(item_id)

            c1, c2, c3 = st.columns(3)
            with c1:
                new_price = st.number_input(
                    "New price",
                    min_value=0.01,
                    value=float(item.price),
                    key="newprice",
                )
            with c2:
                new_qty = st.number_input(
                    "New quantity",
                    min_value=0,
                    value=int(item.quantity),
                    key="newqty",
                )
            with c3:
                st.write("")
                st.write("")
                if st.button("Save Changes"):
                    item.update_price(new_price)
                    item.update_quantity(new_qty)
                    mgr.update_product(item)
                    _set_success_feedback(f"Successfully updated '{item.name}'.")
                    st.rerun()

            if st.button("Delete Product"):
                mgr.remove_product(item_id)
                _set_success_feedback("Product deleted successfully.")
                st.rerun()

    if not inventory:
        st.info("No inventory records yet.")
        return

    st.dataframe(
        [product.to_dict() for product in inventory],
        use_container_width=True,
        hide_index=True,
    )


def _parse_record_date(record):
    """Safely parse a stored timestamp into a date for filtering and reporting."""
    raw = str(record.get("timestamp", ""))
    try:
        return datetime.fromisoformat(raw).date()
    except (TypeError, ValueError):
        return None


def _filter_records(records, start_date, end_date, query=""):
    query = query.strip().lower()
    filtered = []
    for record in records:
        record_date = _parse_record_date(record)
        if record_date is None or not (start_date <= record_date <= end_date):
            continue
        if query and not any(query in str(value).lower() for value in record.values()):
            continue
        filtered.append(record)
    return sorted(filtered, key=lambda record: record.get("timestamp", ""), reverse=True)


def _build_sales_history_pdf(records, start_date, end_date, search_query="", product_filter="All products", payment_filter="All methods"):
    """Create a downloadable PDF for the currently filtered sales history."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28,
        title="UkayClick Sales Transaction Log",
        author="UkayClick",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="UkayGreenTitle", parent=styles["Title"], textColor=colors.HexColor("#173d30"),
        fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=TA_LEFT, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="UkayMeta", parent=styles["Normal"], textColor=colors.HexColor("#52665b"),
        fontSize=8, leading=11, spaceAfter=3,
    ))
    story = [
        Paragraph("UkayClick — Sales Transaction Log", styles["UkayGreenTitle"]),
        Paragraph(f"Report period: {start_date:%b %d, %Y} to {end_date:%b %d, %Y}", styles["UkayMeta"]),
        Paragraph(f"Search: {search_query.strip() or 'None'}  |  Product: {product_filter}  |  Payment method: {payment_filter}", styles["UkayMeta"]),
        Paragraph(f"Transactions: {len(records)}  |  Sales total: ₱{sum(float(t.get('total', 0) or 0) for t in records):,.2f}", styles["UkayMeta"]),
        Spacer(1, 12),
    ]
    headers = ["Transaction ID", "Date & Time", "Product", "Customer", "Qty", "Payment", "Total", "Amount Paid", "Change"]
    rows = [headers]
    for t in records:
        rows.append([
            str(t.get("transaction_id", "")), str(t.get("timestamp", "")),
            str(t.get("product", "")), str(t.get("customer", "")),
            str(t.get("quantity", 0)), str(t.get("payment", "")),
            f"₱{float(t.get('total', 0) or 0):,.2f}",
            f"₱{float(t.get('amount_paid', t.get('total', 0)) or 0):,.2f}",
            f"₱{float(t.get('change', 0) or 0):,.2f}",
        ])
    if len(rows) == 1:
        rows.append(["No transactions found for the selected filters."] + [""] * (len(headers) - 1))
    table = Table(rows, repeatRows=1, colWidths=[82, 112, 88, 78, 34, 55, 67, 76, 62])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5b45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f6f7f3")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#17382e")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d5e0d7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Generated by UkayClick. This report includes sales matching the selected filters.", styles["UkayMeta"]))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def ledger_page():
    _show_success_feedback()
    transactions = load_transactions()
    expenses = load_expenses()
    today = date.today()
    default_start = today.replace(day=1)

    title_col, export_col = st.columns([5, 1.35], vertical_alignment="center")
    with title_col:
        st.title("Ledger & Sales History")
    with export_col:
        export_start = st.session_state.get("ledger_from", default_start)
        export_end = st.session_state.get("ledger_to", today)
        if export_start > export_end:
            export_start, export_end = default_start, today
        export_query = st.session_state.get("ledger_global_search", "")
        export_sales = _filter_records(transactions, export_start, export_end, export_query)
        export_product = st.session_state.get("ledger_product_filter", "All products")
        export_payment = st.session_state.get("ledger_payment_filter", "All methods")
        if export_product != "All products":
            export_sales = [t for t in export_sales if t.get("product") == export_product]
        if export_payment != "All methods":
            export_sales = [t for t in export_sales if t.get("payment") == export_payment]
        pdf_bytes = _build_sales_history_pdf(export_sales, export_start, export_end, export_query, export_product, export_payment)
        st.download_button(
            "Export PDF", data=pdf_bytes,
            file_name=f"ukayclick_sales_{export_start:%Y%m%d}_{export_end:%Y%m%d}.pdf",
            mime="application/pdf", use_container_width=True,
            help="Export the sales transactions matching your current filters.",
        )
    st.caption("Search, filter, and manage recorded sales and expenses.")

    # Global search stays visible above the collapsible filter controls and searches both record types.
    global_query = st.text_input(
        "Search transactions and expenses",
        placeholder="Search transaction ID, expense ID, product, customer, category, description...",
        key="ledger_global_search",
    )

    with st.expander("Find a Transaction"):
        from_col, to_col = st.columns(2)
        with from_col:
            start_date = st.date_input("From date", value=default_start, key="ledger_from")
        with to_col:
            end_date = st.date_input("To date", value=today, key="ledger_to")
        if start_date > end_date:
            st.error("The start date must be on or before the end date.")
            return
        filter_col, payment_col, reset_col = st.columns([1, 1, 0.8])
        product_options = sorted({str(t.get("product", "")) for t in transactions if t.get("product")})
        with filter_col:
            product_filter = st.selectbox("Product", ["All products"] + product_options, key="ledger_product_filter")
        with payment_col:
            payment_filter = st.selectbox("Payment method", ["All methods", "Cash", "GCash", "Other"], key="ledger_payment_filter")
        with reset_col:
            st.write("")
            if st.button("Reset filters", use_container_width=True):
                for key in ("ledger_global_search", "ledger_from", "ledger_to", "ledger_product_filter", "ledger_payment_filter"):
                    st.session_state.pop(key, None)
                st.rerun()

    # Edit/delete controls live beneath Find a Transaction as requested.
    with st.expander("Edit / Delete a Transaction"):
        record_type = st.radio("Record type", ["Sale", "Expense"], horizontal=True, key="ledger_manage_type")
        source_records = transactions if record_type == "Sale" else expenses
        id_field = "transaction_id" if record_type == "Sale" else "expense_id"
        if not source_records:
            st.info(f"There are no {record_type.lower()} records to manage.")
        else:
            record_labels = {
                str(record.get(id_field, f"Record {i + 1}")): record
                for i, record in enumerate(source_records)
            }
            selected_id = st.selectbox("Choose a record", list(record_labels.keys()), key="ledger_manage_record")
            selected = record_labels[selected_id]
            original_timestamp = str(selected.get("timestamp", ""))
            try:
                original_datetime = datetime.fromisoformat(original_timestamp)
            except ValueError:
                original_datetime = datetime.now()
            with st.form(f"edit_record_{record_type}_{selected_id}"):
                edit_date = st.date_input("Transaction date", value=original_datetime.date(), key=f"edit_date_{record_type}_{selected_id}")
                if record_type == "Sale":
                    st.caption(f"Product: {selected.get('product', '')} · Quantity: {selected.get('quantity', 0)} · Total: {money(selected.get('total', 0))}")
                    edit_customer = st.text_input("Customer", value=str(selected.get("customer", "Walk-in")), key=f"edit_customer_{selected_id}")
                    payment_options = ["Cash", "GCash", "Other"]
                    current_payment = selected.get("payment", "Cash")
                    if current_payment not in payment_options:
                        payment_options.append(current_payment)
                    edit_payment = st.selectbox("Payment method", payment_options, index=payment_options.index(current_payment), key=f"edit_payment_{selected_id}")
                    sale_total = float(selected.get("total", 0) or 0)
                    paid_default = float(selected.get("amount_paid", sale_total) or 0)
                    edit_paid = st.number_input("Amount paid", min_value=0.0, value=paid_default, step=10.0, key=f"edit_paid_{selected_id}")
                    save_record = st.form_submit_button("Save Changes", use_container_width=True)
                    if save_record:
                        if edit_payment == "Cash" and edit_paid < sale_total:
                            st.error(f"Amount paid must be at least {money(sale_total)} for a cash sale.")
                        else:
                            selected["timestamp"] = datetime.combine(edit_date, original_datetime.time()).strftime("%Y-%m-%d %H:%M:%S")
                            selected["customer"] = edit_customer.strip() or "Walk-in"
                            selected["payment"] = edit_payment
                            selected["amount_paid"] = round(edit_paid if edit_payment == "Cash" else sale_total, 2)
                            selected["change"] = round(float(selected["amount_paid"]) - sale_total, 2) if edit_payment == "Cash" else 0.0
                            save_transactions(transactions)
                            _set_success_feedback("Sale transaction updated successfully.")
                            st.rerun()
                else:
                    categories = ["Supplies", "Transportation", "Rent", "Utilities", "Packaging", "Other"]
                    current_category = selected.get("category", "Other")
                    if current_category not in categories:
                        categories.append(current_category)
                    edit_category = st.selectbox("Expense category", categories, index=categories.index(current_category), key=f"edit_category_{selected_id}")
                    edit_description = st.text_input("Description", value=str(selected.get("description", "")), key=f"edit_description_{selected_id}")
                    edit_amount = st.number_input("Amount", min_value=0.01, value=max(0.01, float(selected.get("amount", 0.01) or 0.01)), step=10.0, key=f"edit_amount_{selected_id}")
                    save_record = st.form_submit_button("Save Changes", use_container_width=True)
                    if save_record:
                        selected["timestamp"] = datetime.combine(edit_date, original_datetime.time()).strftime("%Y-%m-%d %H:%M:%S")
                        selected["category"] = edit_category
                        selected["description"] = edit_description.strip() or edit_category
                        selected["amount"] = round(edit_amount, 2)
                        save_expenses(expenses)
                        _set_success_feedback("Expense transaction updated successfully.")
                        st.rerun()

            if st.button("Delete Selected Record", type="secondary", use_container_width=True, key=f"delete_record_{record_type}_{selected_id}"):
                if record_type == "Sale":
                    # Restore the sold quantity when the corresponding product still exists.
                    item_id = selected.get("item_id")
                    sold_quantity = int(selected.get("quantity", 0) or 0)
                    if item_id and sold_quantity > 0:
                        inventory_manager = InventoryManager()
                        product = inventory_manager.find_product(item_id)
                        if product is not None:
                            product.update_quantity(product.quantity + sold_quantity)
                            inventory_manager.update_product(product)
                    transactions = [record for record in transactions if str(record.get(id_field, "")) != selected_id]
                    save_transactions(transactions)
                else:
                    expenses = [record for record in expenses if str(record.get(id_field, "")) != selected_id]
                    save_expenses(expenses)
                _set_success_feedback(f"{record_type} record deleted successfully.")
                st.rerun()

    query = global_query
    # The date controls default to this month even while their expander is closed.
    start_date = st.session_state.get("ledger_from", default_start)
    end_date = st.session_state.get("ledger_to", today)
    if start_date > end_date:
        st.error("The start date must be on or before the end date.")
        return
    product_filter = st.session_state.get("ledger_product_filter", "All products")
    payment_filter = st.session_state.get("ledger_payment_filter", "All methods")
    filtered_sales = _filter_records(transactions, start_date, end_date, query)
    if product_filter != "All products":
        filtered_sales = [t for t in filtered_sales if t.get("product") == product_filter]
    if payment_filter != "All methods":
        filtered_sales = [t for t in filtered_sales if t.get("payment") == payment_filter]
    filtered_expenses = _filter_records(expenses, start_date, end_date, query)

    sales_total = sum(float(t.get("total", 0) or 0) for t in filtered_sales)
    expenses_total = sum(float(e.get("amount", 0) or 0) for e in filtered_expenses)
    m1, m2, m3 = st.columns(3)
    m1.metric("Matching sales", len(filtered_sales))
    m2.metric("Sales total", money(sales_total))
    m3.metric("Matching expenses", money(expenses_total))

    sales_tab, expense_tab = st.tabs(["Sales", "Expenses"])
    with sales_tab:
        if filtered_sales:
            display_sales = [{
                "Transaction ID": t.get("transaction_id", ""), "Date & Time": t.get("timestamp", ""),
                "Product": t.get("product", ""), "Customer": t.get("customer", ""),
                "Quantity": t.get("quantity", 0), "Payment": t.get("payment", ""),
                "Total": money(t.get("total", 0)), "Amount Paid": money(t.get("amount_paid", t.get("total", 0))),
                "Change": money(t.get("change", 0)),
            } for t in filtered_sales]
            st.dataframe(display_sales, use_container_width=True, hide_index=True)
        else:
            st.info("No sales match these search terms and filters.")
    with expense_tab:
        if filtered_expenses:
            display_expenses = [{
                "Expense ID": e.get("expense_id", ""), "Date & Time": e.get("timestamp", ""),
                "Category": e.get("category", ""), "Description": e.get("description", ""),
                "Amount": money(e.get("amount", 0)),
            } for e in filtered_expenses]
            st.dataframe(display_expenses, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses match this date range or search.")


def expenses_page():
    st.title("Record Expense")

    category = st.selectbox(
        "Expense category",
        [
            "Supplies",
            "Transportation",
            "Rent",
            "Utilities",
            "Packaging",
            "Other",
        ],
    )
    expense_date = st.date_input(
        "Expense Date",
        value=date.today(),
        help="Choose the date this expense should be recorded under.",
        key="record_expense_date",
    )
    description = st.text_input("Description")
    amount = st.number_input(
        "Amount",
        min_value=0.01,
        step=10.0,
    )

    if st.button("Complete Recording", use_container_width=True):
        ok, msg = ExpenseManager().record_expense(
            category,
            description,
            amount,
            expense_date=expense_date,
        )

        if ok:
            st.success("Expense recorded successfully. You can see it in the Ledger tab.")
        else:
            st.error(msg)


def analysis_page():
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


if not st.session_state.logged_in:
    login_screen()
else:
    # All business records are scoped to the authenticated account.
    set_current_user(st.session_state.user.get_username())

    with st.sidebar:
        st.markdown("## UkayClick")
        st.caption("THRIFT STORE MANAGEMENT")

        navigation_pages = [
            "Dashboard",
            "Process Sale",
            "Inventory",
            "Ledger",
            "Expenses",
            "Reports & Prediction",
        ]
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"
        for nav_page in navigation_pages:
            if st.button(
                nav_page,
                key=f"nav_{nav_page}",
                type="primary" if st.session_state.current_page == nav_page else "secondary",
                use_container_width=True,
            ):
                st.session_state.current_page = nav_page
                st.rerun()
        page = st.session_state.current_page

        st.divider()

        if st.button("Log Out", key="logout_button", use_container_width=True):
            st.session_state.user.logout()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    page_name = page

    if page_name == "Dashboard":
        dashboard()
    elif page_name == "Process Sale":
        sales_page()
    elif page_name == "Inventory":
        inventory_page()
    elif page_name == "Ledger":
        ledger_page()
    elif page_name == "Expenses":
        expenses_page()
    elif page_name == "Reports & Prediction":
        analysis_page()
