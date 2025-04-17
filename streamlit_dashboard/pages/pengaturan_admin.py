import streamlit as st
from components.login_manager import load_credentials, save_credentials

# Check if the user is logged in
if not st.session_state.get("logged_in", False):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Pengaturan Akun Admin")

# Load credentials from the local JSON file
cred = load_credentials()

# Create a form for updating username and password
with st.form("admin_update"):
    new_user = st.text_input("Username baru", value=cred["username"])
    new_pass = st.text_input("Password baru", type="password")
    confirm = st.text_input("Konfirmasi password", type="password")
    submitted = st.form_submit_button("Simpan Perubahan")
    
    if submitted:
        if new_pass == confirm:
            # Save the new credentials to the local file
            save_credentials(new_user, new_pass)
            st.success("Akun berhasil diperbarui.")
        else:
            st.error("Password tidak cocok.")

# Tombol Logout (di sidebar)
with st.sidebar:
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.success("Berhasil logout.")
        st.experimental_rerun()
