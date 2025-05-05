import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image
from components.mongo_utils import fetch_data_from_mongo

st.set_page_config(page_title="Analitik Kelelahan dan Shift", layout="wide")

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

.stats-card {
    background-color: white;
    padding: 1.2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
    height: 100%;
    transition: all 0.3s;
}

.stats-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.section-container {
    background-color: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.2rem;
}

.section-title {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: #333;
    padding-left: 20px;
    font-size: 1.5rem;
    font-weight: 600;
}

.highlight-text {
    background-color: #b3127a;
    color: white;
    padding: 0.8rem;
    border-radius: 10px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 1rem;
}

.trend-highlight {
    display: inline-block;
    padding: 0.5rem 1rem;
    font-weight: bold;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1rem;
}

.spacer {
    height: 15px;
}

.trend-up {
    background-color: #ff77cd;
    color: white;
}

.trend-down {
    background-color: #4CAF50;
    color: white;
}

.trend-stable {
    background-color: #2196F3;
    color: white;
}

.divider {
    height: 1px;
    background-color: #eee;
    margin: 1.5rem 0;
}

@media (max-width: 768px) {
    .stats-card {
        margin-bottom: 1rem;
    }
    
    h1 {
        font-size: 1.5rem;
    }
    
    .section-container {
        padding: 1rem;
    }
    
    .header-space {
        margin-bottom: 1rem;
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

col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists(logo_path):
        st.image(Image.open(logo_path), width=100)
with col2:
    st.title("Analitik Kelelahan dan Shift")

df = fetch_data_from_mongo()

try:
    df['weekday'] = df['timestamp'].dt.day_name()
    hari_mapping = {
        'Monday': 'Senin',
        'Tuesday': 'Selasa',
        'Wednesday': 'Rabu',
        'Thursday': 'Kamis',
        'Friday': 'Jumat',
        'Saturday': 'Sabtu',
        'Sunday': 'Minggu'
    }
    df['hari'] = df['weekday'].map(hari_mapping)
    df['hour'] = df['timestamp'].dt.hour

    st.markdown("<h3 class='section-title'>🕒 Distribusi Microsleep Harian</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
    
    heatmap_data = df.groupby(['hour', 'hari']).size().unstack(fill_value=0)
    
    ordered_days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    for hari in ordered_days:
        if hari not in heatmap_data.columns:
            heatmap_data[hari] = 0
    heatmap_data = heatmap_data[ordered_days]
    
    max_val_idx = heatmap_data.stack().idxmax()
    jam_rawan = f"{max_val_idx[0]:02d}.00"
    hari_rawan = max_val_idx[1]
    
    st.markdown(f"<div class='highlight-text'>⚠️ Jam Rawan: {hari_rawan}, {jam_rawan} ⚠️</div>", unsafe_allow_html=True)
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=[f"{h:02d}:00" for h in heatmap_data.index],
        colorscale=[
            [0.0, "#ffffff"],
            [0.2, "#ffd0ec"],
            [0.5, "#ff77cd"],
            [0.8, "#ff30b8"],
            [1.0, "#b3127a"]
        ],
        colorbar=dict(title='Jumlah Microsleep'),
        hoverongaps=False
    ))
    
    fig_heatmap.update_layout(
        xaxis_title='Hari',
        yaxis_title='Jam (24 Jam)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='stats-card'>
            <h3>Total Events</h3>
            <h2 style='color: #b3127a; font-size: 2.5rem;'>{}</h2>
            <p>Jumlah microsleep terdeteksi</p>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        morning_count = df[(df['hour'] >= 6) & (df['hour'] < 14)].shape[0]
        afternoon_count = df[(df['hour'] >= 14) & (df['hour'] < 22)].shape[0]
        night_count = df[(df['hour'] < 6) | (df['hour'] >= 22)].shape[0]
        
        highest_count = max(morning_count, afternoon_count, night_count)
        highest_shift = "Pagi" if highest_count == morning_count else "Siang" if highest_count == afternoon_count else "Malam"
        
        st.markdown(f"""
        <div class='stats-card'>
            <h3>Shift Rawan</h3>
            <h2 style='color: #b3127a; font-size: 2.5rem;'>{highest_shift}</h2>
            <p>Shift dengan jumlah microsleep tertinggi</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='stats-card'>
            <h3>Jam Puncak</h3>
            <h2 style='color: #b3127a; font-size: 2.5rem;'>{jam_rawan}</h2>
            <p>Jam dengan frekuensi microsleep tertinggi</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>📈 Tren Microsleep Harian</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
    
    df['date'] = df['timestamp'].dt.date
    trend = df.groupby('date').size().reset_index(name='jumlah')
    trend = trend.sort_values('date')
    
    if trend['jumlah'].iloc[-1] > trend['jumlah'].iloc[0]:
        arah_tren = "MENINGKAT 🔺"
        trend_class = "trend-up"
    elif trend['jumlah'].iloc[-1] < trend['jumlah'].iloc[0]:
        arah_tren = "MENURUN 🔽"
        trend_class = "trend-down"
    else:
        arah_tren = "STABIL ⟹"
        trend_class = "trend-stable"
    
    st.markdown(f"<div class='trend-highlight {trend_class}'>{arah_tren}</div>", unsafe_allow_html=True)
    
    fig_line = px.line(
        trend,
        x='date', y='jumlah',
        markers=True,
        labels={"jumlah": "Jumlah Microsleep", "date": "Tanggal"}
    )
    
    fig_line.update_traces(
        line=dict(color='#ff30b8', width=3),
        marker=dict(color='#ff30b8', size=10)
    )
    
    fig_line.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_title="Tanggal",
        yaxis_title="Jumlah Microsleep",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig_line, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_days = trend.shape[0]
        total_incidents = trend['jumlah'].sum()
        daily_avg = round(total_incidents / total_days, 1) if total_days > 0 else 0
        
        st.markdown(f"""
        <div class='stats-card'>
            <h3>Rata-rata Harian</h3>
            <h2 style='color: #b3127a; font-size: 2.5rem;'>{daily_avg}</h2>
            <p>Rata-rata kejadian microsleep per hari</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        max_day = trend.loc[trend['jumlah'].idxmax()]
        
        st.markdown(f"""
        <div class='stats-card'>
            <h3>Hari Tertinggi</h3>
            <h2 style='color: #b3127a; font-size: 2.5rem;'>{max_day['jumlah']}</h2>
            <p>Tanggal {max_day['date'].strftime('%d-%m-%Y')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    st.markdown("<h3 class='section-title'>💡 Rekomendasi Tindakan</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
    
    shift_tabs = st.tabs(["Shift Pagi", "Shift Siang", "Shift Malam"])
    
    with shift_tabs[0]:
        st.markdown("""
        #### Rekomendasi untuk Shift Pagi (06:00-14:00)
        
        **Pola Tidur Optimal:**
        - Tidur pukul 21:00-22:00 malam hari sebelumnya
        - Target 7-8 jam tidur berkualitas
        - Bangun 60-90 menit sebelum shift dimulai
        
        **Jadwal Istirahat:**
        - Istirahat pendek (10 menit) pukul 10:00-10:15
        - Istirahat makan siang (30 menit) pukul 12:00-12:30
        """)
    
    with shift_tabs[1]:
        st.markdown("""
        #### Rekomendasi untuk Shift Siang (14:00-22:00)
        
        **Pola Tidur Optimal:**
        - Tidur malam minimal 6-7 jam (22:30-05:30)
        - Tidur siang pendek (power nap) 20-30 menit sebelum shift
        - Hindari tidur siang lebih dari 45 menit
        
        **Jadwal Istirahat:**
        - Istirahat pendek (15 menit) pukul 16:30-16:45
        - Istirahat makan (30 menit) pukul 19:00-19:30
        """)
    
    with shift_tabs[2]:
        st.markdown("""
        #### Rekomendasi untuk Shift Malam (22:00-06:00)
        
        **Pola Tidur Optimal:**
        - Tidur 4-5 jam sebelum shift dimulai (16:00-20:00)
        - Tidur 3-4 jam segera setelah shift berakhir
        - Kamar tidur gelap total dengan penutup jendela
        
        **Jadwal Istirahat:**
        - Istirahat pendek (15 menit) pukul 00:00-00:15
        - Istirahat makan (20 menit) pukul 02:30-02:50
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data: {e}")
    st.info("Pastikan data yang tersedia lengkap dan valid.")