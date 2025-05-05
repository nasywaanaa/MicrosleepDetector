import streamlit as st
import pandas as pd
from components.mongo_utils import fetch_data_from_mongo
import datetime
import os
from PIL import Image

st.set_page_config(page_title="Log Alert dan Riwayat Microsleep", layout="wide")

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

.filter-container {
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

.badge {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    color: white;
}

.badge-pagi {
    background-color: #4CAF50;
}

.badge-siang {
    background-color: #FFC107;
    color: #333;
}

.badge-malam {
    background-color: #3F51B5;
}

.alert-counter {
    color: #b3127a;
    font-size: 1.2rem;
    font-weight: bold;
}

@media (max-width: 768px) {
    .section-title {
        margin-top: 1rem;
        margin-bottom: 0.8rem;
        font-size: 1.4rem;
    }
    
    .filter-container, .table-container {
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
    st.title("Log Alert dan Riwayat Microsleep")

df = fetch_data_from_mongo()

df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

df['shift'] = df['hour'].apply(tentukan_shift)

df = df[df['status_alert'] == "ON"]

st.markdown("<h3 class='section-title'>🔍 Filter Riwayat Microsleep</h3>", unsafe_allow_html=True)

st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    selected_sopir = st.multiselect("Nama Sopir", options=sorted(df['nama_sopir'].unique()))
    selected_armada = st.multiselect("Armada", options=sorted(df['armada'].unique()))
    selected_shift = st.multiselect("Shift", options=["Shift Pagi", "Shift Siang", "Shift Malam"])

with col2:
    selected_rute = st.multiselect("Rute", options=sorted(df['rute'].unique()))

    df = df.dropna(subset=['date'])

    min_date = df['date'].min()
    max_date = df['date'].max()

    if isinstance(min_date, pd.Timestamp):
        min_date = min_date.date()
    elif not isinstance(min_date, pd.Timestamp) and not isinstance(min_date, datetime.date):
        min_date = None

    if isinstance(max_date, pd.Timestamp):
        max_date = max_date.date()
    elif not isinstance(max_date, pd.Timestamp) and not isinstance(max_date, datetime.date):
        max_date = None

    today = pd.to_datetime("today").date()

    if min_date and max_date and min_date <= today <= max_date:
        default_date = today
    else:
        default_date = max_date if max_date else today

    date_input = st.date_input(
        "Pilih Tanggal (boleh satu atau rentang)",
        value=(default_date, default_date),
        min_value=min_date,
        max_value=max_date
    )

    if not isinstance(date_input, tuple):
        st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")
st.markdown("</div>", unsafe_allow_html=True)

def calculate_alert_frequency(group):
    group = group.sort_values('timestamp')
    group['time_diff'] = group['timestamp'].diff().fillna(pd.Timedelta(minutes=16))
    group['new_event'] = group['time_diff'] > pd.Timedelta(minutes=15)
    group['event_group'] = group['new_event'].cumsum()
    return pd.DataFrame({
        'nama_sopir': [group['nama_sopir'].iloc[0]],
        'armada': [group['armada'].iloc[0]],
        'rute': [group['rute'].iloc[0]],
        'shift': [group['shift'].iloc[0]],
        'frekuensi_microsleep': [group['event_group'].nunique()],
        'jumlah_alert': [len(group)]
    })

if selected_sopir:
    df = df[df['nama_sopir'].isin(selected_sopir)]
if selected_armada:
    df = df[df['armada'].isin(selected_armada)]
if selected_shift:
    df = df[df['shift'].isin(selected_shift)]
if selected_rute:
    df = df[df['rute'].isin(selected_rute)]

if isinstance(date_input, tuple):
    start_date, end_date = date_input
else:
    start_date = end_date = date_input

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

df = df[
    (df['date'] >= start_date.date()) &
    (df['date'] <= end_date.date())
]

result_df = pd.DataFrame()
for name, group in df.groupby(['nama_sopir', 'shift']):
    result = calculate_alert_frequency(group)
    result_df = pd.concat([result_df, result], ignore_index=True)

st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

st.markdown("<h3 class='section-title'>📋 Detail Microsleep per Pengemudi</h3>", unsafe_allow_html=True)

st.markdown("<div class='table-container'>", unsafe_allow_html=True)
if not result_df.empty:
    st.markdown("""
    <div class="highlight-box">
        <p>Berikut adalah data microsleep yang dideteksi dalam periode waktu yang dipilih. 
        Kejadian Microsleep dihitung berdasarkan alert yang terjadi dengan jeda minimal 15 menit.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='overflow-x: auto;'>", unsafe_allow_html=True)
    
    total_incidents = result_df['frekuensi_microsleep'].sum()
    st.markdown(f"<p>Total Kejadian Microsleep: <span class='alert-counter'>{total_incidents}</span></p>", unsafe_allow_html=True)
    
    display_df = result_df.copy()
    display_df['shift'] = display_df['shift'].apply(
        lambda x: f"<span class='badge badge-{'pagi' if x=='Shift Pagi' else 'siang' if x=='Shift Siang' else 'malam'}'>{x}</span>"
    )
    
    display_df.columns = ['Nama Pengemudi', 'Armada', 'Rute', 'Shift', 'Kejadian Microsleep', 'Total Alert']
    
    display_df = display_df.sort_values('Kejadian Microsleep', ascending=False)
    
    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    csv = result_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Unduh Data (CSV)",
        data=csv,
        file_name=f"log_microsleep_{start_date.date()}_to_{end_date.date()}.csv",
        mime='text/csv',
    )
else:
    st.info("Tidak ada data microsleep yang cocok dengan filter yang dipilih.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)