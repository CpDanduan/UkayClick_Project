"""Render Ledger interface."""
from datetime import date
import streamlit as st
from models.inventory import InventoryManager
from repositories.json_repository import load_transactions, save_transactions, load_expenses, save_expenses
from ukayclick_ui import money
from views.common import _set_success_feedback, _show_success_feedback, _filter_records
from views.ledger_helpers import _build_sales_history_pdf

def render_ledger():
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

