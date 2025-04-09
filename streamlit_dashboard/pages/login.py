import streamlit as st
import json

# Load kredensial
with open("admin_config.json") as f:
    creds = json.load(f)

st.set_page_config(page_title="Login Admin", layout="centered")
st.title("Login Admin")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if username == creds["username"] and password == creds["password"]:
        st.session_state["logged_in"] = True
        st.success("Login berhasil!")
        st.switch_page("pages/dashboard_utama.py")
    else:
        st.error("Username atau password salah.")
