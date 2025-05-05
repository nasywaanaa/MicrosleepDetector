import streamlit as st
import os
from PIL import Image

def get_asset_path(filename):
    return os.path.join(os.path.dirname(__file__), 'assets', filename)

sigap_logo_path = get_asset_path('sigap.png')
bangun_icon_path = get_asset_path('bangun.png')

if os.path.exists(sigap_logo_path):
    st.set_page_config(
        page_title="SIGAP - About",
        page_icon=Image.open(sigap_logo_path),
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="SIGAP - About",
        page_icon=Image.open(sigap_logo_path),
        layout="wide"
    )
# 
st.markdown("""
<style>
    /* Base responsive styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Mobile specific adjustments */
    @media (max-width: 640px) {
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
        p, li {
            font-size: 0.9rem !important;
        }
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    
    /* Improve spacing on mobile */
    .stImage {
        margin-bottom: 1rem;
    }
    
    /* Make sure images don't overflow on mobile */
    img {
        max-width: 100%;
        height: auto;
    }
    
    /* Better column layout on mobile */
    @media (max-width: 640px) {
        .row-widget.stHorizontal {
            flex-direction: column;
        }
        .row-widget.stHorizontal > div {
            width: 100% !important;
            margin-bottom: 1rem;
        }
    }
    
    /* Styling for the logout button */
    .logout-btn {
        background-color: #f44336 !important;
        color: white !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 8px 12px !important;
        border-radius: 5px !important;
        transition: all 0.3s !important;
        margin-top: 10px;
    }
    
    .logout-btn:hover {
        background-color: #d32f2f !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

if os.path.exists(sigap_logo_path):
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(Image.open(sigap_logo_path), width=120, use_container_width=True)
    with col2:
        st.title("SIGAP - Sistem Intelligence Gerak Aktivitas Pengemudi")
        st.markdown("<p style='font-size:1rem;'>Solusi Inovatif untuk Keselamatan Transportasi</p>", unsafe_allow_html=True)
else:
    st.title("SIGAP - Sistem Intelligence Gerak Aktivitas Pengemudi")
    st.subheader("Solusi Inovatif untuk Keselamatan Transportasi")

st.markdown("---")
st.header("🔍 Tentang SIGAP")

is_mobile = st.columns([3, 1])[1].checkbox("Tampilan Mobile", value=False, help="Aktifkan untuk tampilan optimal di perangkat mobile")

if is_mobile:
    st.markdown("""
    ### Mengapa SIGAP diperlukan?
    
    Microsleep atau tidur mikro adalah kondisi tertidur secara tidak sadar selama beberapa detik hingga 30 detik.
    Kondisi ini sangat berbahaya terutama bagi pengemudi kendaraan umum seperti bus dan angkutan lainnya.
    """)
    
    if os.path.exists(bangun_icon_path):
        st.image(Image.open(bangun_icon_path), width=150, use_container_width=True)
    
    st.markdown("""
    Data menunjukkan bahwa **80% kecelakaan lalu lintas** disebabkan oleh pengemudi yang mengantuk atau 
    mengalami microsleep. SIGAP hadir sebagai solusi teknologi untuk mendeteksi dan mencegah 
    kondisi berbahaya ini.
    """)
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        ### Mengapa SIGAP diperlukan?
        
        Microsleep atau tidur mikro adalah kondisi tertidur secara tidak sadar selama beberapa detik hingga 30 detik.
        Kondisi ini sangat berbahaya terutama bagi pengemudi kendaraan umum seperti bus dan angkutan lainnya.
        
        Data menunjukkan bahwa **20-30% kecelakaan lalu lintas** disebabkan oleh pengemudi yang mengantuk atau 
        mengalami microsleep. SIGAP hadir sebagai solusi teknologi untuk mendeteksi dan mencegah 
        kondisi berbahaya ini.
        """)
    with col2:
        if os.path.exists(bangun_icon_path):
            st.image(Image.open(bangun_icon_path), width=200, use_container_width=True)

st.markdown("---")
st.header("🛠️ Komponen Sistem SIGAP")

hardware_tab, software_tab = st.tabs(["Hardware", "Software"])

with hardware_tab:
    st.markdown("""
    ### Hardware
    - **Kamera Deteksi Wajah**: Memantau kondisi mata dan wajah pengemudi
    - **Sensor Posisi Kepala**: Mendeteksi gerakan kepala yang menandakan kantuk
    - **Alarm Microsleep**: Membangunkan pengemudi saat terdeteksi microsleep
    - **Sistem Komunikasi**: Mengirim data secara real-time ke pusat kontrol
    """)

with software_tab:
    st.markdown("""
    ### Software
    - **Algorithm Deteksi Microsleep**: Menganalisis pola mata dan gerakan wajah
    - **Dashboard Monitoring**: Memvisualisasikan data dan memberikan peringatan
    - **Sistem Klasifikasi Pengemudi**: Mengelompokkan pengemudi berdasarkan risiko
    - **Rekomendasi Shift**: Mengoptimalkan jadwal kerja pengemudi
    """)

# How it works - numbered list works well on mobile
st.markdown("---")
st.header("⚙️ Cara Kerja SIGAP")

# Card layout for better mobile display
st.markdown("""
<div style="background-color:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px;">
    <ol style="margin-left: 20px;">
        <li><strong>Deteksi</strong>: Kamera dan sensor memantau kondisi pengemudi secara real-time</li>
        <li><strong>Analisis</strong>: Algoritma AI menganalisis data untuk mendeteksi tanda-tanda microsleep</li>
        <li><strong>Peringatan</strong>: Sistem memberikan peringatan kepada pengemudi saat terdeteksi risiko microsleep</li>
        <li><strong>Pencatatan</strong>: Data microsleep dicatat dan dikirim ke sistem pusat</li>
        <li><strong>Analitik</strong>: Dashboard menganalisis pola untuk manajemen risiko jangka panjang</li>
        <li><strong>Rekomendasi</strong>: Sistem memberikan rekomendasi jadwal dan istirahat yang optimal</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.header("✅ Manfaat SIGAP")

with st.expander("Bagi Perusahaan", expanded=True):
    st.markdown("""
    - Mengurangi risiko kecelakaan
    - Mengoptimalkan jadwal pengemudi
    - Meningkatkan kualitas layanan
    - Mengurangi biaya asuransi
    """)

with st.expander("Bagi Pengemudi", expanded=True):
    st.markdown("""
    - Meningkatkan keselamatan kerja
    - Jadwal kerja yang lebih optimal
    - Mengurangi risiko kelelahan
    - Peningkatan kualitas istirahat
    """)

with st.expander("Bagi Masyarakat", expanded=True):
    st.markdown("""
    - Transportasi yang lebih aman
    - Mengurangi kecelakaan lalu lintas
    - Meningkatkan kepercayaan publik
    - Mendukung transportasi berkelanjutan
    """)

foto_path = get_asset_path('foto.jpg')
if os.path.exists(foto_path):
    st.image(Image.open(foto_path), caption="Tim IoTelligence", use_container_width=True)

st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 14px; margin-top: 10px; padding: 10px;">
        Dikembangkan oleh <b>Tim IoTelligence</b> – Institut Teknologi Bandung<br>
        Hubungi kami di <a href="mailto:sigap@gmailcom">sigap@gmail.com</a>
    </div>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>Admin Panel</h2>", unsafe_allow_html=True)
    
    if st.session_state.get("logged_in", False):
        st.success(f"Logged in as {st.session_state.get('username', 'Admin')}")
        
        if st.button("Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/Dashboard.py")
        
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state["logged_in"] = False
            if "username" in st.session_state:
                del st.session_state["username"]
            
            st.success("Berhasil logout!")
            st.rerun()
    else:
        st.info("Silakan login untuk mengakses dashboard dan fitur administrasi.")
        
        if st.button("Login ke Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/Login.py")