import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.set_page_config(page_title="Analitik Kelelahan dan Shift", layout="wide")
st.title("Analitik Kelelahan dan Shift")

# Load data
df = pd.read_csv("assets/microsleep_log.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

# ==========================
# 📊 Heatmap Jam vs Hari
# ==========================
st.subheader("🕒 Heatmap Jam Rawan dalam Seminggu")

# Ekstrak hari dalam bahasa Indonesia
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

# Buat pivot table jam vs hari
heatmap_data = df.groupby(['hour', 'hari']).size().unstack(fill_value=0)

# Urutkan kolom hari
ordered_days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
for hari in ordered_days:
    if hari not in heatmap_data.columns:
        heatmap_data[hari] = 0
heatmap_data = heatmap_data[ordered_days]

# Temukan jam dan hari dengan jumlah microsleep tertinggi
max_val_idx = heatmap_data.stack().idxmax()  # (hour, hari)
jam_rawan = f"{max_val_idx[0]:02d}.00"
hari_rawan = max_val_idx[1]
judul_risiko = f"Jam Rawan: {hari_rawan}, {jam_rawan}"

# Tambahkan judul ke streamlit
st.subheader(judul_risiko)

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
    height=600
)

st.plotly_chart(fig_heatmap, use_container_width=True)

# ==========================
# 📈 Tren Jumlah Harian
# ==========================
st.subheader("📈 Tren Jumlah Microsleep Harian")

# Hitung jumlah microsleep per tanggal
trend = df.groupby('date').size().reset_index(name='jumlah')

# Pastikan data diurutkan berdasarkan tanggal
trend = trend.sort_values('date')

# Tentukan tren naik/turun
if trend['jumlah'].iloc[-1] > trend['jumlah'].iloc[0]:
    arah_tren = "MENINGKAT"
elif trend['jumlah'].iloc[-1] < trend['jumlah'].iloc[0]:
    arah_tren = "TURUN"
else:
    arah_tren = "STABIL"

# Buat judul dinamis
judul = f"Trend Microsleep: {arah_tren.upper()}"

st.subheader(judul)

# Buat line chart
fig_line = px.line(
    trend,
    x='date', y='jumlah',
    markers=True,
    labels={"jumlah": "Jumlah Microsleep", "date": "Tanggal"}
)

# Ubah warna garis dan marker menjadi #ff30b8
fig_line.update_traces(
    line=dict(color='#ff30b8'),
    marker=dict(color='#ff30b8')
)

# Tampilkan chart di Streamlit
st.plotly_chart(fig_line, use_container_width=True)