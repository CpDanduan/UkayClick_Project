"""Coordinate authentication, account scope, and view navigation."""
import streamlit as st
from models.auth import Authentication
from repositories.json_repository import set_current_user
from views.login_view import render_login
from views.dashboard_view import render_dashboard
from views.sales_view import render_sales
from views.inventory_view import render_inventory
from views.ledger_view import render_ledger
from views.expenses_view import render_expenses
from views.reports_view import render_reports

def run_app():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("last_receipt", None)
    auth = Authentication()
    if not st.session_state.logged_in:
        render_login(auth)
        return
    set_current_user(st.session_state.user.get_username())
    with st.sidebar:
        st.markdown("## UkayClick")
        pages = ["Dashboard", "Process Sale", "Inventory", "Ledger", "Expenses", "Reports & Prediction"]
        st.session_state.setdefault("current_page", "Dashboard")
        for page in pages:
            if st.button(page, key=f"nav_{page}", type="primary" if st.session_state.current_page == page else "secondary", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        selected = st.session_state.current_page
        st.divider()
        if st.button("Log Out", key="logout_button", use_container_width=True):
            st.session_state.user.logout()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
    routes = {"Dashboard": render_dashboard, "Process Sale": render_sales, "Inventory": render_inventory, "Ledger": render_ledger, "Expenses": render_expenses, "Reports & Prediction": render_reports}
    routes.get(selected, render_dashboard)()
