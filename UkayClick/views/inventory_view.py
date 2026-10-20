"""Render Inventory interface."""
import streamlit as st
from models.inventory import InventoryManager, Product
from ukayclick_ui import money
from views.common import _set_success_feedback, _show_success_feedback

def render_inventory():
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

