import streamlit as st
from components.login_manager import load_credentials, save_credentials
import streamlit as st

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Pengaturan Akun Admin")

cred = load_credentials()
with st.form("admin_update"):
    new_user = st.text_input("Username baru", value=cred["username"])
    new_pass = st.text_input("Password baru", type="password")
    confirm = st.text_input("Konfirmasi password", type="password")
    submitted = st.form_submit_button("Simpan Perubahan")
    if submitted:
        if new_pass == confirm:
            save_credentials(new_user, new_pass)
            st.success("Akun berhasil diperbarui.")
        else:
            st.error("Password tidak cocok.")

# Tombol Logout (di sidebar)
with st.sidebar:
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.success("Berhasil logout.")
        st.switch_page("pages/home.py")
