"""Render Login interface."""
import streamlit as st

def render_login(auth):
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

