import streamlit as st
import json

# Path to the local admin_config.json file (make sure to adjust this path if it's in a different directory)
CONFIG_FILE = "admin_config.json"

# Load credentials from the local JSON file
def load_credentials():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Credentials file not found.")
        return {"username": "", "password": ""}

# Set the page configuration
st.set_page_config(page_title="Login Admin", layout="centered")
st.title("Login Admin")

# Load credentials from the local JSON file
creds = load_credentials()

# Input fields for username and password
username = st.text_input("Username")
password = st.text_input("Password", type="password")

# Button for login
if st.button("Login"):
    if username == creds["username"] and password == creds["password"]:
        st.session_state["logged_in"] = True
        st.success("Login berhasil!")
        st.experimental_rerun()  # Or use st.switch_page("pages/dashboard_utama.py") if you have page navigation
    else:
        st.error("Username atau password salah.")
