"""Render Sales interface."""
from datetime import date
import streamlit as st
from models.inventory import InventoryManager
from models.sales import process_sale
from models.ereceipt import EReceipt
from ukayclick_ui import money

def render_sales():
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

