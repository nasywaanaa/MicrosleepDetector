import streamlit as st
import os

st.set_page_config(page_title="Microsleep Dashboard", layout="wide")

st.title("Selamat Datang di Microsleep Detection System")

st.markdown("""
Dashboard ini membantu memantau dan menganalisis deteksi microsleep pada sopir.
""")

image_path = os.path.join(os.path.dirname(__file__), 'assets', 'foto.jpg')
st.image(image_path, use_container_width=True)


# Setelah semua visualisasi dan tabel...
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 14px; margin-top: 10px;">
        Dibuat oleh <b>Tim IoTelligence</b> – Institut Teknologi Bandung
    </div>
""", unsafe_allow_html=True)

# Tombol Logout (di sidebar)
with st.sidebar:
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.success("Berhasil logout.")
        st.experimental_rerun()
