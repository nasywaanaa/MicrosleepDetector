import streamlit as st

st.set_page_config(page_title="Microsleep Dashboard", layout="wide")

st.title("Selamat Datang di Microsleep Detection System")

st.markdown("""
Dashboard ini membantu memantau dan menganalisis deteksi microsleep pada sopir.
""")

st.image("assets/anjay.jpg", use_container_width=True)  # bisa atur width sesuai kebutuhan
# st.image("https://linkgambar.com/logo.png", width=200)

# Setelah semua visualisasi dan tabel...
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 14px; margin-top: 10px;">
        Dibuat oleh <b>Tim IoTelligence</b> – Institut Teknologi Bandung
    </div>
""", unsafe_allow_html=True)

