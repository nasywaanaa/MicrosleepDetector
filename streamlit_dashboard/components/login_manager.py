import streamlit as st
import json

CONFIG_FILE = "admin_config.json"

def load_credentials():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_credentials(username, password):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"username": username, "password": password}, f)

def login():
    st.title("🔐 Login Admin")
    credentials = load_credentials()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == credentials["username"] and password == credentials["password"]:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Username atau password salah")

def require_login():
    if not st.session_state.get("logged_in"):
        st.error("Akses ditolak. Silakan login terlebih dahulu.")
        st.stop()

