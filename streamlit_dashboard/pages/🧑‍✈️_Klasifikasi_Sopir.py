import streamlit as st
import pandas as pd
import plotly.express as px
from components.mongo_utils import fetch_data_from_mongo
import datetime

# Check if the user is logged in
if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Klasifikasi dan Evaluasi Sopir")

# Load data from MongoDB
df = fetch_data_from_mongo()

# ===== FILTER TANGGAL =====
st.subheader("Filter Tanggal")
# Ensure 'date' column is in correct format
df['date'] = pd.to_datetime(df['timestamp']).dt.date

# Get the minimum and maximum dates
min_date = df['date'].min()  # Already a datetime.date object
max_date = df['date'].max()  # Already a datetime.date object

# Get today's date
today = pd.to_datetime("today").date()

# Set the default date
default_date = today if min_date <= today <= max_date else max_date

lihat_semua = st.checkbox("Lihat Semua Tanggal", value=True)

if not lihat_semua:
    date_input = st.date_input(
        "Pilih Tanggal (boleh satu atau rentang)",
        value=(default_date, default_date),
        min_value=min_date,
        max_value=max_date
    )

    # Display warning if the user hasn't selected a range
    if not isinstance(date_input, tuple):
        st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")

    # Handle one or two selected dates
    if isinstance(date_input, tuple):
        start_date, end_date = date_input
    else:
        start_date = end_date = date_input

    # Convert start_date and end_date to datetime.date for comparison
    start_date = start_date if isinstance(start_date, datetime.date) else start_date.date()
    end_date = end_date if isinstance(end_date, datetime.date) else end_date.date()

    # Filter the DataFrame
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    st.caption(f"Menampilkan data dari {start_date.strftime('%d %b %Y')} hingga {end_date.strftime('%d %b %Y')}")
else:
    filtered_df = df.copy()
    st.caption("Menampilkan data untuk semua tanggal.")

# ===== PROSES LANJUT DENGAN DATA YANG SUDAH DIFILTER =====

# Add shift column
def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

filtered_df['shift'] = filtered_df['timestamp'].dt.hour.apply(tentukan_shift)

# Count the most frequent shift per driver
shift_terbanyak = (
    filtered_df.groupby(['nama_sopir', 'shift'])
    .size()
    .reset_index(name='jumlah_shift')
    .sort_values(['nama_sopir', 'jumlah_shift'], ascending=[True, False])
    .drop_duplicates(subset='nama_sopir')
    .rename(columns={'shift': 'shift_terbanyak'})
)[['nama_sopir', 'shift_terbanyak']]

# Count microsleep occurrences per driver
classification = filtered_df.groupby('nama_sopir').size().reset_index(name='jumlah')

# Calculate average and classify based on rules
rata2 = classification['jumlah'].mean()

def klasifikasi(x):
    if x == 0:
        return 'Aman'
    elif x <= rata2:
        return 'Waspada'
    else:
        return 'Bahaya!'

classification['kategori'] = classification['jumlah'].apply(klasifikasi)

# Merge dominant shift data
classification = classification.merge(shift_terbanyak, on='nama_sopir', how='left')

# Prepare data for bar chart (ensure all categories are displayed)
kategori_order = ['Aman', 'Waspada', 'Bahaya!']
kategori_summary = classification.groupby('kategori').size().reindex(kategori_order, fill_value=0).reset_index(name='jumlah')

# Display histogram
st.subheader("Distribusi Sopir Berdasarkan Kategori")
fig = px.bar(
    kategori_summary,
    x='kategori', y='jumlah', color='kategori',
    category_orders={'kategori': kategori_order},
    labels={'jumlah': 'Jumlah Sopir'}
)
st.plotly_chart(fig)

# Display detailed table based on category selection
selected = st.selectbox("Lihat Detail Kategori", kategori_order)
st.dataframe(classification[classification['kategori'] == selected])
