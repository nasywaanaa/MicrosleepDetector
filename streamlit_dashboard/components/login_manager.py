import streamlit as st
import json
import os

# Correct path to the admin_config.json file
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'admin_config.json')  # Adjust this path

# Function to load credentials from the local JSON file
def load_credentials():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Credentials file not found: {CONFIG_FILE}")
        return {"username": "", "password": ""}

# Function to save updated credentials to the local JSON file
def save_credentials(username, password):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"username": username, "password": password}, f)
    except Exception as e:
        st.error(f"Failed to save credentials: {e}")

# Function to handle login
def login():
    st.title("🔐 Login Admin")
    
    # Load credentials from the local JSON file
    credentials = load_credentials()
    
    # User input for login
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == credentials["username"] and password == credentials["password"]:
            # Store logged-in status in session state
            st.session_state["logged_in"] = True
            st.success("Login berhasil!")
            st.experimental_rerun()  # Or use st.switch_page("pages/dashboard_utama.py") if you have page navigation
        else:
            st.error("Username atau password salah")

# Function to check if user is logged in, otherwise deny access
def require_login():
    if not st.session_state.get("logged_in"):
        st.error("Akses ditolak. Silakan login terlebih dahulu.")
        st.stop()
