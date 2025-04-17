import streamlit as st
import pandas as pd

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Log Alert dan Riwayat Microsleep")

# Load data
df = pd.read_csv("assets/microsleep_log.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

# Tambah kolom shift
def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

df['shift'] = df['hour'].apply(tentukan_shift)

# Filter hanya data dengan status_alert = ON
df = df[df['status_alert'] == "ON"]

# Filter Sidebar / Expander
st.subheader("Filter Riwayat Microsleep")
with st.expander("Filter Data"):
    col1, col2 = st.columns(2)

    with col1:
        selected_sopir = st.multiselect("Nama Sopir", options=sorted(df['nama_sopir'].unique()))
        selected_armada = st.multiselect("Armada", options=sorted(df['armada'].unique()))
        selected_shift = st.multiselect("Shift", options=["Shift Pagi", "Shift Siang", "Shift Malam"])

    with col2:
        selected_rute = st.multiselect("Rute", options=sorted(df['rute'].unique()))

        # === Filter Tanggal Menggunakan Kalender (Rentang atau Satu Hari) ===
        df['date'] = pd.to_datetime(df['date'])
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        today = pd.to_datetime("today").date()
        default_date = today if min_date <= today <= max_date else max_date

        date_input = st.date_input(
            "Pilih Tanggal (boleh satu atau rentang)",
            value=(default_date, default_date),
            min_value=min_date,
            max_value=max_date
        )

        # Tampilkan warning friendly jika user belum pilih rentang
        if not isinstance(date_input, tuple):
            st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")


# === Terapkan Filter ===
if selected_sopir:
    df = df[df['nama_sopir'].isin(selected_sopir)]
if selected_armada:
    df = df[df['armada'].isin(selected_armada)]
if selected_shift:
    df = df[df['shift'].isin(selected_shift)]
if selected_rute:
    df = df[df['rute'].isin(selected_rute)]

# Filter berdasarkan tanggal input (satu atau rentang)
if isinstance(date_input, tuple):
    start_date, end_date = date_input
else:
    start_date = end_date = date_input

df = df[
    (df['date'] >= pd.to_datetime(start_date)) &
    (df['date'] <= pd.to_datetime(end_date))
]

# === Tampilkan Hasil ===
st.subheader("Hasil Filter Riwayat Microsleep (Status ON)")
st.dataframe(df[['nama_sopir', 'timestamp', 'armada', 'rute', 'shift', 'status_alert']])