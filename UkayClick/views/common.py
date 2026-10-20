"""Shared helpers for Streamlit views."""
from datetime import datetime
import streamlit as st

def _set_success_feedback(message):
    """Keep action confirmation visible after a Streamlit rerun."""
    st.session_state["ukayclick_success_feedback"] = message


def _show_success_feedback():
    """Display and clear the latest one-time success confirmation."""
    message = st.session_state.pop("ukayclick_success_feedback", None)
    if message:
        st.success(message)


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

