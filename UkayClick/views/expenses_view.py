"""Render Expenses interface."""
from datetime import date
import streamlit as st
from models.expenses import ExpenseManager

def render_expenses():
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

