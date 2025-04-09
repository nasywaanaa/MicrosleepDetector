import streamlit as st
import pandas as pd

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.set_page_config(page_title="Dashboard Utama", layout="wide")
st.title("Dashboard Utama")

# Load data
data = pd.read_csv("assets/microsleep_log.csv")
data['timestamp'] = pd.to_datetime(data['timestamp'])
data['date'] = data['timestamp'].dt.date
data['hour'] = data['timestamp'].dt.hour

# Tambahkan kolom shift
def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

data['shift'] = data['hour'].apply(tentukan_shift)

# --- Filter Tanggal ---
st.subheader("🗓️ Filter Tanggal")
# all_dates = sorted(data['date'].unique())
# selected_date = st.selectbox("Pilih Tanggal", options=["Semua Tanggal"] + [str(d) for d in all_dates])

# Pastikan kolom 'date' bertipe datetime
data['date'] = pd.to_datetime(data['date'])

# Ambil batas tanggal dari data
min_date = data['date'].min().date()
max_date = data['date'].max().date()

# Tentukan default (pakai hari ini kalau masih dalam range)
today = pd.to_datetime("today").date()
default_date = today if min_date <= today <= max_date else max_date

# Input kalender — bisa 1 tanggal atau 2
date_input = st.date_input(
    "Pilih Tanggal (boleh satu atau rentang)",
    value=(default_date, default_date),  # default: 1 hari rentang
    min_value=min_date,
    max_value=max_date
)

# Tangani 1 tanggal atau rentang
if isinstance(date_input, tuple):
    start_date, end_date = date_input
else:
    start_date = end_date = date_input  # user hanya pilih 1 tanggal

# Filter data
filtered_data = data[
    (data['date'] >= pd.to_datetime(start_date)) &
    (data['date'] <= pd.to_datetime(end_date))
]

# --- Hitung Data Summary ---
sopir_microsleep = filtered_data[filtered_data['status_alert'] == 'ON']['nama_sopir'].nunique()
total_armada = filtered_data['armada'].nunique()
sopir_shift = filtered_data.groupby('shift')['nama_sopir'].nunique()

# --- Ringkasan Metrik Harian ---
st.markdown("### 📊 Ringkasan Operasional")
col1, col2, col3, col4, col5 = st.columns(5)

def render_card(title, icon, value, bgcolor):
    st.markdown(f"""
    <div style="
        background-color: {bgcolor};
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 1.1rem; font-weight: 600; color: #000;">{title}</div>
        <div style="font-size: 2rem; padding-top: 0.2rem;">
            <span style="margin-right: 0.3rem;">{icon}</span><strong style="color:#fff;">{value}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col1:
    render_card("Microsleep", "🛑", sopir_microsleep, "#ffa3ddff")
with col2:
    render_card("Armada", "🚌", total_armada, "#ff77cdff")
with col3:
    render_card("Shift Pagi", "🌅", sopir_shift.get('Shift Pagi', 0), "#e620a3ff")
with col4:
    render_card("Shift Siang", "⛅", sopir_shift.get('Shift Siang', 0), "#cc1990ff")
with col5:
    render_card("Shift Malam", "🌙", sopir_shift.get('Shift Malam', 0), "#b3127aff")

st.markdown("---")
