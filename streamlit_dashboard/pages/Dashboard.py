import streamlit as st
import pandas as pd
import os
from PIL import Image
from components.mongo_utils import fetch_data_from_mongo
import datetime

st.set_page_config(
    page_title="SIGAP - Dashboard",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .main .block-container { 
        padding-top: 1rem;
        padding-bottom: 1.5rem; 
    }
    
    .section-container {
        margin-bottom: 1rem;
    }
    
    .header-space {
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.12);
    }
    
    .metric-title {
        font-size: 1rem;
        font-weight: 600;
        color: #555;
        margin-bottom: 0.6rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #b3127a;
    }
    
    .metric-icon {
        font-size: 1.8rem;
        margin-bottom: 0.6rem;
    }
    
    .section-title {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: #333;
        padding-left: 20px;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .filter-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    .divider {
        height: 1px;
        background-color: #eee;
        margin: 1.5rem 0;
    }
    
    .spacer {
        height: 15px;
    }
    
    .risk-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        padding: 1rem;
        margin-bottom: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s ease;
    }
    
    .risk-card:hover {
        transform: translateY(-3px);
    }
    
    .recommendation-box {
        padding: 1.2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-top: 1.2rem;
        border-left: 5px solid #b3127a;
    }
    
    @media (max-width: 768px) {
        .metric-card {
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 1.8rem;
        }
        
        .metric-icon {
            font-size: 1.8rem;
        }
        
        .header-space {
            margin-bottom: 1rem;
        }
        
        .filter-container {
            padding: 1rem;
        }
        
        .section-title {
            margin-top: 1rem;
            margin-bottom: 0.8rem;
            font-size: 1.4rem;
        }
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.markdown("<div class='header-space'></div>", unsafe_allow_html=True)
logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'bangun.png')
logo_img = Image.open(logo_path) if os.path.exists(logo_path) else None

col1, col2 = st.columns([1, 5])
with col1:
    if logo_img:
        st.image(logo_img, width=100)
with col2:
    st.title("Dashboard SIGAP")

data = fetch_data_from_mongo()

try:
    if 'date' not in data.columns and 'timestamp' in data.columns:
        data['date'] = pd.to_datetime(data['timestamp']).dt.date
    elif 'date' not in data.columns:
        data['date'] = pd.to_datetime(datetime.datetime.now().date())
    
    if 'hour' not in data.columns and 'timestamp' in data.columns:
        data['hour'] = pd.to_datetime(data['timestamp']).dt.hour
    elif 'hour' not in data.columns:
        data['hour'] = datetime.datetime.now().hour
    
    def tentukan_shift(jam):
        if 6 <= jam < 14:
            return "Shift Pagi"
        elif 14 <= jam < 22:
            return "Shift Siang"
        else:
            return "Shift Malam"
    
    if 'shift' not in data.columns:
        data['shift'] = data['hour'].apply(tentukan_shift)
    
    data['date'] = pd.to_datetime(data['date'])
    
except Exception as e:
    st.error(f"Error processing data: {e}")
    st.info("Attempting to recover with default values...")
    
    if 'date' not in data.columns:
        data['date'] = pd.to_datetime(datetime.datetime.now().date())
    if 'hour' not in data.columns:
        data['hour'] = datetime.datetime.now().hour
    if 'shift' not in data.columns:
        data['shift'] = 'Shift Pagi'

st.markdown("<div class='section-container'>", unsafe_allow_html=True)
st.markdown("<h3 class='section-title'>🔍 Filter Data</h3>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    
    filter_col1, filter_col2 = st.columns([2, 1])
    
    with filter_col1:
        try:
            min_date = data['date'].min()
            max_date = data['date'].max()
        except:
            min_date = datetime.datetime.now().date() - datetime.timedelta(days=30)
            max_date = datetime.datetime.now().date()
        
        today = pd.Timestamp(datetime.datetime.now().date())
        default_date = today if min_date <= today <= max_date else max_date
        
        date_input = st.date_input(
            "Pilih Rentang Tanggal",
            value=(default_date, default_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(date_input, tuple):
            start_date, end_date = date_input
        else:
            start_date = end_date = date_input
    
    with filter_col2:
        try:
            all_drivers = sorted(data['nama_sopir'].unique())
        except:
            all_drivers = []
            
        selected_driver = st.multiselect("Filter Pengemudi (Opsional)", options=all_drivers, default=[])
    
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

try:
    filtered_data = data[
        (data['date'] >= pd.to_datetime(start_date)) &
        (data['date'] <= pd.to_datetime(end_date))
    ]

    if selected_driver:
        filtered_data = filtered_data[filtered_data['nama_sopir'].isin(selected_driver)]
except Exception as e:
    st.error(f"Error filtering data: {e}")
    filtered_data = data 

st.markdown("<div class='section-container'>", unsafe_allow_html=True)
st.markdown("<h3 class='section-title'>📊 Ringkasan Operasional</h3>", unsafe_allow_html=True)

try:
    sopir_microsleep = filtered_data[filtered_data['status_alert'] == 'ON']['nama_sopir'].nunique() if 'status_alert' in filtered_data.columns else 0
    total_microsleep = filtered_data[filtered_data['status_alert'] == 'ON'].shape[0] if 'status_alert' in filtered_data.columns else 0
    total_armada = filtered_data['armada'].nunique() if 'armada' in filtered_data.columns else 0
    total_sopir = filtered_data['nama_sopir'].nunique() if 'nama_sopir' in filtered_data.columns else 0
    
    if 'shift' in filtered_data.columns and 'nama_sopir' in filtered_data.columns:
        sopir_shift = filtered_data.groupby('shift')['nama_sopir'].nunique()
    else:
        sopir_shift = pd.Series([0, 0, 0], index=['Shift Pagi', 'Shift Siang', 'Shift Malam'])
    
except Exception as e:
    st.error(f"Error calculating metrics: {e}")
    sopir_microsleep = 0
    total_microsleep = 0
    total_armada = 0
    total_sopir = 0
    sopir_shift = pd.Series([0, 0, 0], index=['Shift Pagi', 'Shift Siang', 'Shift Malam'])

metrics = [
    {"title": "Total Microsleep", "icon": "🛑", "value": total_microsleep, "color": "#ff77cd"},
    {"title": "Pengemudi Terdampak", "icon": "🧑‍✈️", "value": sopir_microsleep, "color": "#e620a3"},
    {"title": "Total Armada", "icon": "🚌", "value": total_armada, "color": "#cc1990"},
    {"title": "Total Pengemudi", "icon": "👥", "value": total_sopir, "color": "#b3127a"}
]

col1, col2, col3, col4 = st.columns(4)
cols = [col1, col2, col3, col4]

for i, metric in enumerate(metrics):
    with cols[i]:
        st.markdown(f"""
        <div class='metric-card' style='border-top: 5px solid {metric["color"]};'>
            <div class='metric-icon'>{metric["icon"]}</div>
            <div class='metric-title'>{metric["title"]}</div>
            <div class='metric-value'>{metric["value"]}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

st.markdown("<div class='section-container'>", unsafe_allow_html=True)
st.markdown("<h3 class='section-title'>⏱️ Distribusi Per Shift</h3>", unsafe_allow_html=True)

shift_col1, shift_col2, shift_col3 = st.columns(3)

shift_data = [
    {"title": "Shift Pagi (06:00-14:00)", "icon": "🌅", "value": sopir_shift.get('Shift Pagi', 0), "color": "#ff77cd"},
    {"title": "Shift Siang (14:00-22:00)", "icon": "☀️", "value": sopir_shift.get('Shift Siang', 0), "color": "#e620a3"},
    {"title": "Shift Malam (22:00-06:00)", "icon": "🌙", "value": sopir_shift.get('Shift Malam', 0), "color": "#b3127a"}
]

shift_cols = [shift_col1, shift_col2, shift_col3]

for i, shift in enumerate(shift_data):
    with shift_cols[i]:
        st.markdown(f"""
        <div class='metric-card' style='border-top: 5px solid {shift["color"]};'>
            <div class='metric-icon'>{shift["icon"]}</div>
            <div class='metric-title'>{shift["title"]}</div>
            <div class='metric-value'>{shift["value"]}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='section-container'>", unsafe_allow_html=True)
try:
    if 'status_alert' in filtered_data.columns:
        microsleep_data = filtered_data[filtered_data['status_alert'] == 'ON']
    else:
        microsleep_data = pd.DataFrame()  
    
    if not microsleep_data.empty and 'nama_sopir' in microsleep_data.columns:
        driver_microsleep = microsleep_data.groupby('nama_sopir').size().reset_index(name='jumlah')
        driver_microsleep = driver_microsleep.sort_values('jumlah', ascending=False).head(5)
        
        st.markdown("<h3 class='section-title'>⚠️ Pengemudi Dengan Risiko Tertinggi</h3>", unsafe_allow_html=True)
        
        risk_data = []
        for i, row in driver_microsleep.iterrows():
            risk_level = "Tinggi" if row['jumlah'] > 5 else "Sedang" if row['jumlah'] > 2 else "Rendah"
            risk_color = "#F44336" if risk_level == "Tinggi" else "#FFC107" if risk_level == "Sedang" else "#4CAF50"
            
            risk_data.append({
                "nama": row['nama_sopir'],
                "jumlah": row['jumlah'],
                "level": risk_level,
                "color": risk_color
            })
        
        for risk in risk_data:
            st.markdown(f"""
            <div class="risk-card">
                <div>
                    <h4 style="margin: 0;">{risk["nama"]}</h4>
                    <p style="margin: 0; color: #666;">Jumlah Microsleep: {risk["jumlah"]}</p>
                </div>
                <div style="
                    background-color: {risk["color"]};
                    color: white;
                    padding: 0.4rem 0.8rem;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 0.9rem;
                ">
                    {risk["level"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="recommendation-box">
            <p style="margin: 0; font-weight: 600; font-size: 1.1rem;">💡 Rekomendasi</p>
            <p style="margin-top: 0.6rem; line-height: 1.4;">
            Evaluasi pola shift untuk pengemudi dengan risiko tinggi dan pertimbangkan untuk memberikan istirahat tambahan
            atau pelatihan kesadaran microsleep.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Tidak ada data microsleep dalam rentang tanggal yang dipilih.")
except Exception as e:
    st.error(f"Error analyzing risk data: {e}")
    st.info("Tidak dapat menampilkan analisis risiko.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)