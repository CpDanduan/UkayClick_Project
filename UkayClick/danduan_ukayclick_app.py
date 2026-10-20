"""UkayClick Streamlit application entry point."""
import streamlit as st
from controllers.app_controller import run_app
from ukayclick_ui import apply_style

st.set_page_config(page_title="UkayClick", layout="wide")
apply_style()
run_app()
