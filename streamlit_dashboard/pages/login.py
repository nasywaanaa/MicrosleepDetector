import streamlit as st

# Load kredensial dari secrets
creds = st.secrets["admin"]

st.set_page_config(page_title="Login Admin", layout="centered")
st.title("Login Admin")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if username == creds["username"] and password == creds["password"]:
        st.session_state["logged_in"] = True
        st.success("Login berhasil!")
        st.switch_page("pages/dashboard_utama.py")
        # Tombol Logout (di sidebar)
        with st.sidebar:
            if st.button("Logout"):
                st.session_state["logged_in"] = False
                st.success("Berhasil logout.")
                st.experimental_rerun()
    else:
        st.error("Username atau password salah.")
