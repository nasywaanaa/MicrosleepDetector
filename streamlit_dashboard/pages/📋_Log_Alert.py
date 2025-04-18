import streamlit as st
import pandas as pd
from mongodb_connection import get_mongo_client
import datetime  # Add this import

# Check if the user is logged in
if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.title("Log Alert dan Riwayat Microsleep")

# Fetch data from MongoDB
collection = get_mongo_client()

# Function to fetch data from MongoDB
def fetch_data_from_mongo():
    # Query to get data from the collection
    query = {}
    projection = {"_id": 0}  # Exclude _id field
    cursor = collection.find(query, projection)
    
    # Convert to DataFrame
    data = pd.DataFrame(list(cursor))
    data['timestamp'] = pd.to_datetime(data['timestamp'])  # Ensure 'timestamp' is datetime
    return data

# Load data from MongoDB
df = fetch_data_from_mongo()

# Add 'date' column by extracting the date from 'timestamp'
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour

# Add shift column based on hour
def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

df['shift'] = df['hour'].apply(tentukan_shift)

# Filter only data where status_alert == "ON"
df = df[df['status_alert'] == "ON"]

# ================================
# Filter Sidebar / Expander
# ================================
st.subheader("Filter Riwayat Microsleep")
with st.expander("Filter Data"):
    col1, col2 = st.columns(2)

    with col1:
        selected_sopir = st.multiselect("Nama Sopir", options=sorted(df['nama_sopir'].unique()))
        selected_armada = st.multiselect("Armada", options=sorted(df['armada'].unique()))
        selected_shift = st.multiselect("Shift", options=["Shift Pagi", "Shift Siang", "Shift Malam"])

    with col2:
        selected_rute = st.multiselect("Rute", options=sorted(df['rute'].unique()))

        # Ensure there are no NaT values in the 'date' column and filter out invalid rows
        df = df.dropna(subset=['date'])

        # Safely get the min and max date after filtering
        min_date = df['date'].min()
        max_date = df['date'].max()

        # Ensure 'min_date' and 'max_date' are valid datetime.date objects
        if isinstance(min_date, pd.Timestamp):
            min_date = min_date.date()
        elif not isinstance(min_date, pd.Timestamp) and not isinstance(min_date, datetime.date):
            min_date = None  # Handle invalid min_date

        if isinstance(max_date, pd.Timestamp):
            max_date = max_date.date()
        elif not isinstance(max_date, pd.Timestamp) and not isinstance(max_date, datetime.date):
            max_date = None  # Handle invalid max_date

        today = pd.to_datetime("today").date()

        # Default date: choose today if within the range of min_date and max_date
        if min_date and max_date and min_date <= today <= max_date:
            default_date = today
        else:
            default_date = max_date if max_date else today  # Fallback to today if max_date is invalid

        # Date input filter
        date_input = st.date_input(
            "Pilih Tanggal (boleh satu atau rentang)",
            value=(default_date, default_date),
            min_value=min_date,
            max_value=max_date
        )

        # Display friendly warning if the user hasn't selected a range
        if not isinstance(date_input, tuple):
            st.info("Klik dua kali tanggal jika hanya ingin memilih satu hari, atau pilih dua tanggal untuk rentang waktu.")


# ================================
# Apply Filters
# ================================
if selected_sopir:
    df = df[df['nama_sopir'].isin(selected_sopir)]
if selected_armada:
    df = df[df['armada'].isin(selected_armada)]
if selected_shift:
    df = df[df['shift'].isin(selected_shift)]
if selected_rute:
    df = df[df['rute'].isin(selected_rute)]

# Convert 'start_date' and 'end_date' to pandas Timestamp
if isinstance(date_input, tuple):
    start_date, end_date = date_input
else:
    start_date = end_date = date_input

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data based on the selected date range
df = df[
    (df['date'] >= start_date.date()) &  # Convert to date for comparison
    (df['date'] <= end_date.date())  # Convert to date for comparison
]

# ================================
# Display Filtered Results
# ================================
st.subheader("Hasil Filter Riwayat Microsleep (Status ON)")
st.dataframe(df[['nama_sopir', 'timestamp', 'armada', 'rute', 'shift', 'status_alert']])
