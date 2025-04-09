import streamlit as st
import pandas as pd
import plotly.express as px

if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Klasifikasi dan Evaluasi Sopir")

# Load data
df = pd.read_csv("assets/microsleep_log.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['date'] = df['timestamp'].dt.date

# ===== FILTER TANGGAL =====
st.subheader("Filter Tanggal")
df['date'] = pd.to_datetime(df['date'])  # pastikan format datetime
min_date = df['date'].min().date()
max_date = df['date'].max().date()
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

    # Tampilkan warning friendly jika user belum pilih rentang
    if not isinstance(date_input, tuple):
        st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")

    # Tangani satu atau dua tanggal
    if isinstance(date_input, tuple):
        start_date, end_date = date_input
    else:
        start_date = end_date = date_input

    filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]

    st.caption(f"Menampilkan data dari {start_date.strftime('%d %b %Y')} hingga {end_date.strftime('%d %b %Y')}")
else:
    filtered_df = df.copy()
    st.caption("Menampilkan data untuk semua tanggal.")

# ===== PROSES LANJUT DENGAN DATA YANG SUDAH DIFILTER =====

# Tambahkan kolom shift
def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

filtered_df['shift'] = filtered_df['timestamp'].dt.hour.apply(tentukan_shift)

# Hitung shift terbanyak per sopir
shift_terbanyak = (
    filtered_df.groupby(['nama_sopir', 'shift'])
    .size()
    .reset_index(name='jumlah_shift')
    .sort_values(['nama_sopir', 'jumlah_shift'], ascending=[True, False])
    .drop_duplicates(subset='nama_sopir')
    .rename(columns={'shift': 'shift_terbanyak'})
)[['nama_sopir', 'shift_terbanyak']]

# Hitung jumlah microsleep per sopir
classification = filtered_df.groupby('nama_sopir').size().reset_index(name='jumlah')

# Hitung rata-rata & klasifikasikan berdasarkan aturan
rata2 = classification['jumlah'].mean()

def klasifikasi(x):
    if x == 0:
        return 'Aman'
    elif x <= rata2:
        return 'Waspada'
    else:
        return 'Bahaya!'

classification['kategori'] = classification['jumlah'].apply(klasifikasi)

# Gabungkan shift dominan
classification = classification.merge(shift_terbanyak, on='nama_sopir', how='left')

# Siapkan data untuk bar chart (pastikan semua kategori tampil)
kategori_order = ['Aman', 'Waspada', 'Bahaya!']
kategori_summary = classification.groupby('kategori').size().reindex(kategori_order, fill_value=0).reset_index(name='jumlah')

# Tampilkan histogram
st.subheader("Distribusi Sopir Berdasarkan Kategori")
fig = px.bar(
    kategori_summary,
    x='kategori', y='jumlah', color='kategori',
    category_orders={'kategori': kategori_order},
    labels={'jumlah': 'Jumlah Sopir'}
)
st.plotly_chart(fig)

# Tampilkan tabel detail berdasarkan kategori
selected = st.selectbox("Lihat Detail Kategori", kategori_order)
st.dataframe(classification[classification['kategori'] == selected])
