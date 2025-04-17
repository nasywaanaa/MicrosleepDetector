import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from mongodb_connection import get_mongo_client

# Check if the user is logged in
if not st.session_state.get("logged_in"):
    st.warning("Anda harus login untuk mengakses halaman ini.")
    st.stop()

st.set_page_config(page_title="Analitik Kelelahan dan Shift", layout="wide")
st.title("Analitik Kelelahan dan Shift")

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

# ==========================
# 📊 Heatmap Jam vs Hari
# ==========================
st.subheader("🕒 Heatmap Jam Rawan dalam Seminggu")

# Extract day of the week in Indonesian
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

# Ensure 'hour' column is created correctly
df['hour'] = df['timestamp'].dt.hour  # Extract the hour from the timestamp

# Create pivot table for hour vs day
heatmap_data = df.groupby(['hour', 'hari']).size().unstack(fill_value=0)

# Order columns by days of the week
ordered_days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
for hari in ordered_days:
    if hari not in heatmap_data.columns:
        heatmap_data[hari] = 0
heatmap_data = heatmap_data[ordered_days]

# Find the hour and day with the highest number of microsleeps
max_val_idx = heatmap_data.stack().idxmax()  # (hour, day)
jam_rawan = f"{max_val_idx[0]:02d}.00"
hari_rawan = max_val_idx[1]
judul_risiko = f"Jam Rawan: {hari_rawan}, {jam_rawan}"

# Add the title to Streamlit
st.subheader(judul_risiko)

# Create heatmap
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

# Ensure 'date' column is created from 'timestamp'
df['date'] = df['timestamp'].dt.date  # Extract the date part from the timestamp

# Calculate the number of microsleep per date
trend = df.groupby('date').size().reset_index(name='jumlah')

# Sort the data by date
trend = trend.sort_values('date')

# Determine the trend (increase, decrease, or stable)
if trend['jumlah'].iloc[-1] > trend['jumlah'].iloc[0]:
    arah_tren = "MENINGKAT"
elif trend['jumlah'].iloc[-1] < trend['jumlah'].iloc[0]:
    arah_tren = "TURUN"
else:
    arah_tren = "STABIL"

# Create dynamic title for trend
judul = f"Trend Microsleep: {arah_tren.upper()}"

st.subheader(judul)

# Create line chart
fig_line = px.line(
    trend,
    x='date', y='jumlah',
    markers=True,
    labels={"jumlah": "Jumlah Microsleep", "date": "Tanggal"}
)

# Update line and marker color
fig_line.update_traces(
    line=dict(color='#ff30b8'),
    marker=dict(color='#ff30b8')
)

# Display the chart in Streamlit
st.plotly_chart(fig_line, use_container_width=True)
