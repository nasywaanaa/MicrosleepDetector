import streamlit as st
import pandas as pd
import plotly.express as px
from components.mongo_utils import fetch_data_from_mongo
import datetime
import os
from PIL import Image

st.set_page_config(page_title="Klasifikasi dan Evaluasi Sopir", layout="wide")

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

.filter-container {
    background-color: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.2rem;
}

.chart-container {
    background-color: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.2rem;
}

.table-container {
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

.divider {
    height: 1px;
    background-color: #eee;
    margin: 1.5rem 0;
}

.spacer {
    height: 15px;
}

.highlight-box {
    background-color: #f8f9fa;
    border-left: 5px solid #b3127a;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
}

.category-aman {
    background-color: #4CAF50;
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    display: inline-block;
}

.category-waspada {
    background-color: #FFC107;
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    display: inline-block;
}

.category-bahaya {
    background-color: #F44336;
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    display: inline-block;
}

@media (max-width: 768px) {
    .section-title {
        margin-top: 1rem;
        margin-bottom: 0.8rem;
        font-size: 1.4rem;
    }
    
    .filter-container, .chart-container, .table-container {
        padding: 1rem;
    }
    
    .header-space {
        margin-bottom: 1rem;
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
    st.title("Klasifikasi dan Evaluasi Sopir")

df = fetch_data_from_mongo()

st.markdown("<h3 class='section-title'>🔍 Filter Data</h3>", unsafe_allow_html=True)

st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
df['date'] = pd.to_datetime(df['timestamp']).dt.date

min_date = df['date'].min() 
max_date = df['date'].max() 

today = pd.to_datetime("today").date()

default_date = today if min_date <= today <= max_date else max_date

lihat_semua = st.checkbox("Lihat Semua Tanggal", value=True)

if not lihat_semua:
    date_input = st.date_input(
        "Pilih Tanggal (boleh satu atau rentang)",
        value=(default_date, default_date),
        min_value=min_date,
        max_value=max_date
    )

    if not isinstance(date_input, tuple):
        st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")

    if isinstance(date_input, tuple):
        start_date, end_date = date_input
    else:
        start_date = end_date = date_input

    start_date = start_date if isinstance(start_date, datetime.date) else start_date.date()
    end_date = end_date if isinstance(end_date, datetime.date) else end_date.date()

    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    st.caption(f"Menampilkan data dari {start_date.strftime('%d %b %Y')} hingga {end_date.strftime('%d %b %Y')}")
else:
    filtered_df = df.copy()
    st.caption("Menampilkan data untuk semua tanggal.")
st.markdown("</div>", unsafe_allow_html=True)

def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

filtered_df['shift'] = filtered_df['timestamp'].dt.hour.apply(tentukan_shift)

shift_terbanyak = (
    filtered_df.groupby(['nama_sopir', 'shift'])
    .size()
    .reset_index(name='jumlah_shift')
    .sort_values(['nama_sopir', 'jumlah_shift'], ascending=[True, False])
    .drop_duplicates(subset='nama_sopir')
    .rename(columns={'shift': 'shift_terbanyak'})
)[['nama_sopir', 'shift_terbanyak']]

filtered_df = filtered_df[filtered_df['status_alert'] == "ON"]

def calculate_event_frequency_for_driver(driver_data):
    if driver_data.empty:
        return 0
    
    driver_data = driver_data.sort_values('timestamp')
    
    driver_data['time_diff'] = driver_data['timestamp'].diff().fillna(pd.Timedelta(minutes=16))
    
    driver_data['new_event'] = driver_data['time_diff'] > pd.Timedelta(minutes=15)
    
    event_count = driver_data['new_event'].sum() + 1 
    
    return event_count

nama_sopir_list = filtered_df['nama_sopir'].unique()
hasil_klasifikasi = []

for nama in nama_sopir_list:
    driver_data = filtered_df[filtered_df['nama_sopir'] == nama]
    jumlah_event = calculate_event_frequency_for_driver(driver_data)
    hasil_klasifikasi.append({
        'nama_sopir': nama,
        'jumlah': jumlah_event
    })

classification = pd.DataFrame(hasil_klasifikasi)

rata2 = classification['jumlah'].mean() if not classification.empty else 0

def klasifikasi(x):
    if x == 0:
        return 'Aman'
    elif x <= rata2:
        return 'Waspada'
    else:
        return 'Bahaya!'

classification['kategori'] = classification['jumlah'].apply(klasifikasi)

classification = classification.merge(shift_terbanyak, on='nama_sopir', how='left')

kategori_order = ['Aman', 'Waspada', 'Bahaya!']
kategori_summary = classification.groupby('kategori').size().reindex(kategori_order, fill_value=0).reset_index(name='jumlah')

st.markdown("<h3 class='section-title'>📊 Distribusi Sopir Berdasarkan Kategori</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    aman_count = kategori_summary[kategori_summary['kategori'] == 'Aman']['jumlah'].values[0]
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #4CAF50;'>
        <h3>Sopir Kategori Aman</h3>
        <h2 style='color: #4CAF50; font-size: 2.5rem;'>{aman_count}</h2>
        <p>Tidak terdeteksi microsleep</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    waspada_count = kategori_summary[kategori_summary['kategori'] == 'Waspada']['jumlah'].values[0]
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #FFC107;'>
        <h3>Sopir Kategori Waspada</h3>
        <h2 style='color: #FFC107; font-size: 2.5rem;'>{waspada_count}</h2>
        <p>Terdeteksi microsleep dalam rata-rata</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    bahaya_count = kategori_summary[kategori_summary['kategori'] == 'Bahaya!']['jumlah'].values[0]
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #F44336;'>
        <h3>Sopir Kategori Bahaya</h3>
        <h2 style='color: #F44336; font-size: 2.5rem;'>{bahaya_count}</h2>
        <p>Terdeteksi microsleep di atas rata-rata</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
st.markdown(f"""
<div class="highlight-box">
    <p><strong>Informasi Klasifikasi:</strong> Pengemudi dikategorikan berdasarkan frekuensi microsleep</p>
    <ul>
        <li><span class="category-aman">Aman</span>: Tidak terdeteksi microsleep</li>
        <li><span class="category-waspada">Waspada</span>: Terdeteksi microsleep ≤ {rata2:.1f} kali (rata-rata)</li>
        <li><span class="category-bahaya">Bahaya!</span>: Terdeteksi microsleep > {rata2:.1f} kali (di atas rata-rata)</li>
    </ul>
</div>
""", unsafe_allow_html=True)

fig = px.bar(
    kategori_summary,
    x='kategori', y='jumlah', 
    color='kategori',
    color_discrete_map={'Aman': '#4CAF50', 'Waspada': '#FFC107', 'Bahaya!': '#F44336'},
    category_orders={'kategori': kategori_order},
    labels={'jumlah': 'Jumlah Sopir', 'kategori': 'Kategori'}
)

fig.update_layout(
    height=400,
    margin=dict(l=40, r=40, t=40, b=40),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<h3 class='section-title'>🧑‍✈️ Detail Pengemudi per Kategori</h3>", unsafe_allow_html=True)

st.markdown("<div class='table-container'>", unsafe_allow_html=True)
selected = st.selectbox("Pilih Kategori untuk Melihat Detail", kategori_order)

display_df = classification[classification['kategori'] == selected].copy()

if len(display_df) == 0:
    st.info(f"Tidak ada pengemudi dalam kategori {selected}")
else:
    display_df = display_df.rename(columns={
        'nama_sopir': 'Nama Pengemudi',
        'jumlah': 'Jumlah Microsleep',
        'shift_terbanyak': 'Shift Utama'
    })
    
    st.dataframe(
        display_df[['Nama Pengemudi', 'Jumlah Microsleep', 'Shift Utama']], 
        use_container_width=True,
        height=400
    )

    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"Unduh Daftar Pengemudi Kategori {selected}",
        data=csv,
        file_name=f"pengemudi_kategori_{selected.lower()}.csv",
        mime='text/csv',
    )
st.markdown("</div>", unsafe_allow_html=True)

if selected == "Bahaya!":
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    st.markdown("""
    <h4>Rekomendasi Tindakan untuk Pengemudi Kategori Bahaya</h4>
    <ol>
        <li>Evaluasi jadwal shift dan pertimbangkan untuk mengubah pola shift</li>
        <li>Berikan waktu istirahat tambahan di tengah shift</li>
        <li>Lakukan pemeriksaan kesehatan untuk mendeteksi masalah tidur</li>
        <li>Berikan pelatihan tentang pentingnya istirahat dan tidur yang cukup</li>
        <li>Pertimbangkan untuk memberikan pendampingan khusus selama shift</li>
    </ol>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)