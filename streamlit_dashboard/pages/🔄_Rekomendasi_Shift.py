import streamlit as st
import pandas as pd
import numpy as np
from components.mongo_utils import fetch_data_from_mongo
import datetime
import os
from PIL import Image
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

st.set_page_config(page_title="Rekomendasi Shift Otomatis", layout="wide")

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

.info-container {
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

.shift-pill {
    display: inline-block;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    color: white;
    margin-right: 0.5rem;
}

.pagi-shift {
    background-color: #4CAF50;
}

.siang-shift {
    background-color: #FFC107;
    color: #333;
}

.malam-shift {
    background-color: #3F51B5;
}

.alert-level {
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.9rem;
    display: inline-block;
}

.low-risk {
    background-color: #4CAF50;
}

.med-risk {
    background-color: #FFC107;
    color: #333;
}

.high-risk {
    background-color: #F44336;
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

@media (max-width: 768px) {
    .section-title {
        margin-top: 1rem;
        margin-bottom: 0.8rem;
        font-size: 1.4rem;
    }
    
    .filter-container, .table-container, .info-container {
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
    st.title("Rekomendasi Shift Otomatis")

df = fetch_data_from_mongo()

df['date'] = pd.to_datetime(df['timestamp']).dt.date
df['hour'] = df['timestamp'].dt.hour

def tentukan_shift(jam):
    if 6 <= jam < 14:
        return "Shift Pagi"
    elif 14 <= jam < 22:
        return "Shift Siang"
    else:
        return "Shift Malam"

df['shift'] = df['hour'].apply(tentukan_shift)

def calculate_alert_frequency(group):
    group = group.sort_values('timestamp')
    group['time_diff'] = group['timestamp'].diff().fillna(pd.Timedelta(minutes=16))
    group['new_event'] = group['time_diff'] > pd.Timedelta(minutes=15)
    group['event_group'] = group['new_event'].cumsum()
    return group['event_group'].nunique()

alert_df = df[df['status_alert'] == "ON"].copy()

if alert_df.empty:
    st.error("Tidak ada data alert yang tersedia untuk analisis. Pastikan database memiliki data yang valid.")
    st.stop()

st.markdown("<h3 class='section-title'>🔍 Parameter Rekomendasi Shift</h3>", unsafe_allow_html=True)

st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    min_driver_per_shift = st.number_input("Minimal Pengemudi per Shift", min_value=1, value=2)
    balance_importance = st.slider("Prioritas Keseimbangan Shift", min_value=0.0, max_value=1.0, value=0.5, 
                                  help="0 = Prioritaskan keamanan, 1 = Prioritaskan keseimbangan jumlah")

with col2:
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    if isinstance(min_date, pd.Timestamp):
        min_date = min_date.date()
    if isinstance(max_date, pd.Timestamp):
        max_date = max_date.date()
    
    today = pd.to_datetime("today").date()
    default_date = today if min_date <= today <= max_date else max_date
    
    date_range = st.date_input(
        "Rentang Data untuk Analisis",
        value=(min_date, default_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    
    start_date = pd.to_datetime(start_date).date()
    end_date = pd.to_datetime(end_date).date()

st.markdown("</div>", unsafe_allow_html=True)

filtered_alert_df = alert_df[
    (alert_df['date'] >= start_date) &
    (alert_df['date'] <= end_date)
]

driver_stats = []

for driver, group in filtered_alert_df.groupby('nama_sopir'):
    microsleep_count = calculate_alert_frequency(group)
    total_alerts = len(group)
    
    shift_counts = group['shift'].value_counts()
    morning_shift = shift_counts.get('Shift Pagi', 0)
    afternoon_shift = shift_counts.get('Shift Siang', 0)
    night_shift = shift_counts.get('Shift Malam', 0)
    
    morning_alerts = len(group[group['shift'] == 'Shift Pagi'])
    afternoon_alerts = len(group[group['shift'] == 'Shift Siang'])
    night_alerts = len(group[group['shift'] == 'Shift Malam'])
    
    hours = group['hour'].values
    early_morning_alert = sum((hours >= 0) & (hours < 6))
    morning_alert = sum((hours >= 6) & (hours < 12))
    afternoon_alert = sum((hours >= 12) & (hours < 18))
    evening_alert = sum((hours >= 18) & (hours < 24))
    
    driver_stats.append({
        'nama_sopir': driver,
        'microsleep_events': microsleep_count,
        'total_alerts': total_alerts,
        'morning_shift': morning_shift,
        'afternoon_shift': afternoon_shift,
        'night_shift': night_shift,
        'morning_alerts': morning_alerts,
        'afternoon_alerts': afternoon_alerts,
        'night_alerts': night_alerts,
        'early_morning_alert': early_morning_alert,
        'morning_alert': morning_alert,
        'afternoon_alert': afternoon_alert,
        'evening_alert': evening_alert,
        'current_primary_shift': shift_counts.idxmax() if not shift_counts.empty else 'Tidak ada data'
    })

drivers_df = pd.DataFrame(driver_stats)

if drivers_df.empty:
    st.error("Tidak ada data yang cukup untuk analisis dalam rentang waktu yang dipilih.")
    st.stop()

drivers_df = drivers_df.fillna(0)

def classify_risk(microsleep_events):
    if microsleep_events == 0:
        return "Rendah"
    elif microsleep_events <= 3:
        return "Sedang"
    else:
        return "Tinggi"

drivers_df['risk_level'] = drivers_df['microsleep_events'].apply(classify_risk)

features = [
    'microsleep_events', 'morning_alerts', 'afternoon_alerts', 'night_alerts',
    'early_morning_alert', 'morning_alert', 'afternoon_alert', 'evening_alert'
]

X = drivers_df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=0, n_init=10)
clusters = kmeans.fit_predict(X_scaled)
drivers_df['cluster'] = clusters

def determine_worst_shift(row):
    shifts = {
        'Shift Pagi': row['morning_alerts'],
        'Shift Siang': row['afternoon_alerts'],
        'Shift Malam': row['night_alerts']
    }
    return max(shifts, key=shifts.get)

def determine_best_shift(row):
    shifts = {
        'Shift Pagi': row['morning_alerts'],
        'Shift Siang': row['afternoon_alerts'],
        'Shift Malam': row['night_alerts']
    }
    return min(shifts, key=shifts.get)

drivers_df['worst_shift'] = drivers_df.apply(determine_worst_shift, axis=1)
drivers_df['best_shift'] = drivers_df.apply(determine_best_shift, axis=1)

for idx, row in drivers_df.iterrows():
    if row['risk_level'] == 'Tinggi' and row['best_shift'] == row['current_primary_shift']:
        shifts = ['Shift Pagi', 'Shift Siang', 'Shift Malam']
        shifts.remove(row['worst_shift'])  
        if row['current_primary_shift'] in shifts:
            shifts.remove(row['current_primary_shift']) 
        
        if shifts: 
            drivers_df.at[idx, 'best_shift'] = shifts[0]

drivers_df['recommended_shift'] = drivers_df['best_shift']

def ensure_minimum_per_shift(df, min_per_shift=1):
    shifts = ['Shift Pagi', 'Shift Siang', 'Shift Malam']
    counts = df['recommended_shift'].value_counts()

    deficit_shifts = [s for s in shifts if s not in counts.index or counts[s] < min_per_shift]
    
    if not deficit_shifts:
        return df
    
    for deficit_shift in deficit_shifts:
        needed = min_per_shift - counts.get(deficit_shift, 0)

        excess_shifts = [s for s in shifts if s in counts.index and counts[s] > min_per_shift]
        
        if not excess_shifts:
            excess_shifts = [s for s in shifts if s in counts.index and counts[s] > 0 and s != deficit_shift]
        
        if not excess_shifts:
            current_shift_drivers = df[df['current_primary_shift'] == deficit_shift]
            if not current_shift_drivers.empty:
                current_shift_drivers = current_shift_drivers.sort_values('microsleep_events')
                for idx in current_shift_drivers.index[:min_per_shift]:
                    df.at[idx, 'recommended_shift'] = deficit_shift
                continue
            else:
                sorted_drivers = df.sort_values('microsleep_events')
                for idx in sorted_drivers.index[:needed]:
                    df.at[idx, 'recommended_shift'] = deficit_shift
                continue
            
        candidate_drivers = []
        
        current_shift_drivers = df[(df['current_primary_shift'] == deficit_shift) & 
                                  (df['recommended_shift'] != deficit_shift)]
        
        current_shift_drivers = current_shift_drivers.sort_values('microsleep_events')
        candidate_drivers.extend(current_shift_drivers.index.tolist())
        
        if len(candidate_drivers) < needed:
            for shift in excess_shifts:
                for risk_level in ['Rendah', 'Sedang', 'Tinggi']:
                    candidates = df[(df['recommended_shift'] == shift) & 
                                    (df['risk_level'] == risk_level) &
                                    (df.index.isin(candidate_drivers) == False)]  
                    
                    if risk_level == 'Tinggi':
                        safer_candidates = candidates[candidates['worst_shift'] != deficit_shift]
                        if not safer_candidates.empty:
                            candidates = safer_candidates
                    
                    candidates = candidates.sort_values('microsleep_events')
                    candidate_drivers.extend(candidates.index.tolist())
                    
                    if len(candidate_drivers) >= needed:
                        break
                
                if len(candidate_drivers) >= needed:
                    break
        
        if len(candidate_drivers) < needed:
            additional_candidates = df[~df.index.isin(candidate_drivers)].sort_values('microsleep_events')
            candidate_drivers.extend(additional_candidates.index.tolist())
        
        for i in range(min(needed, len(candidate_drivers))):
            df.at[candidate_drivers[i], 'recommended_shift'] = deficit_shift
        
        counts = df['recommended_shift'].value_counts()
    
    counts = df['recommended_shift'].value_counts()
    for shift in shifts:
        if shift not in counts or counts[shift] == 0:
            best_candidate = df.sort_values('microsleep_events').iloc[0]
            df.at[best_candidate.name, 'recommended_shift'] = shift
    
    return df

high_risk_drivers = drivers_df[drivers_df['risk_level'] == 'Tinggi'].copy()

for idx, row in high_risk_drivers.iterrows():
    if row['current_primary_shift'] == row['worst_shift']:
        alternative_shifts = ['Shift Pagi', 'Shift Siang', 'Shift Malam']
        alternative_shifts.remove(row['worst_shift'])
        
        shift_alerts = {
            'Shift Pagi': row['morning_alerts'],
            'Shift Siang': row['afternoon_alerts'],
            'Shift Malam': row['night_alerts']
        }
        
        best_alt = min(alternative_shifts, key=lambda s: shift_alerts.get(s, 0))
        drivers_df.at[idx, 'recommended_shift'] = best_alt

drivers_df = ensure_minimum_per_shift(drivers_df, min_driver_per_shift)

if balance_importance > 0:  
    total_drivers = len(drivers_df)
    target_per_shift = max(min_driver_per_shift, total_drivers // 3)
    
    max_iterations = 20
    iteration = 0
    
    shift_counts = drivers_df['recommended_shift'].value_counts().to_dict()
    for shift in ['Shift Pagi', 'Shift Siang', 'Shift Malam']:
        if shift not in shift_counts:
            shift_counts[shift] = 0
    
    while (max(shift_counts.values()) - min(shift_counts.values()) > 1) and (iteration < max_iterations):
        iteration += 1
        
        max_shift = max(shift_counts, key=shift_counts.get)
        min_shift = min(shift_counts, key=shift_counts.get)

        if shift_counts[max_shift] <= min_driver_per_shift:
            break
            
        candidates = drivers_df[(drivers_df['recommended_shift'] == max_shift) & 
                               (drivers_df['worst_shift'] != min_shift)]
        
        if candidates.empty:
            candidates = drivers_df[drivers_df['recommended_shift'] == max_shift]
            
        if candidates.empty:
            break
            
        moved = False
        for risk in ['Rendah', 'Sedang', 'Tinggi']:
            risk_candidates = candidates[candidates['risk_level'] == risk]
            
            if not risk_candidates.empty:
                risk_candidates = risk_candidates.sort_values('microsleep_events')
                idx = risk_candidates.index[0]
                drivers_df.at[idx, 'recommended_shift'] = min_shift
                
                shift_counts[max_shift] -= 1
                shift_counts[min_shift] += 1
                
                moved = True
                break
                
        if not moved:
            break
        
        if max(shift_counts.values()) - min(shift_counts.values()) <= 1:
            break

final_counts = drivers_df['recommended_shift'].value_counts().to_dict()
for shift in ['Shift Pagi', 'Shift Siang', 'Shift Malam']:
    if shift not in final_counts:
        final_counts[shift] = 0
        
    if final_counts[shift] < min_driver_per_shift:
        needed = min_driver_per_shift - final_counts[shift]
        excess_shifts = [s for s in ['Shift Pagi', 'Shift Siang', 'Shift Malam'] 
                         if s != shift and final_counts.get(s, 0) > min_driver_per_shift]
        
        if not excess_shifts:
            excess_shifts = [s for s in ['Shift Pagi', 'Shift Siang', 'Shift Malam'] 
                            if s != shift and final_counts.get(s, 0) > 0]
        
        candidates = []
        for excess_shift in excess_shifts:
            shift_drivers = drivers_df[drivers_df['recommended_shift'] == excess_shift].sort_values('microsleep_events')
            candidates.extend(shift_drivers.index.tolist())
            
            if len(candidates) >= needed:
                break
                
        for i in range(min(needed, len(candidates))):
            drivers_df.at[candidates[i], 'recommended_shift'] = shift

risk_counts = drivers_df['risk_level'].value_counts()

st.markdown("<h3 class='section-title'>📊 Ringkasan Analisis Pengemudi</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #4CAF50;'>
        <h3>Pengemudi Risiko Rendah</h3>
        <h2 style='color: #4CAF50; font-size: 2.5rem;'>{risk_counts.get('Rendah', 0)}</h2>
        <p>Tidak terdeteksi microsleep</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #FFC107;'>
        <h3>Pengemudi Risiko Sedang</h3>
        <h2 style='color: #FFC107; font-size: 2.5rem;'>{risk_counts.get('Sedang', 0)}</h2>
        <p>1-3 kejadian microsleep</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #F44336;'>
        <h3>Pengemudi Risiko Tinggi</h3>
        <h2 style='color: #F44336; font-size: 2.5rem;'>{risk_counts.get('Tinggi', 0)}</h2>
        <p>Lebih dari 3 kejadian microsleep</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)

st.markdown("<div class='info-container'>", unsafe_allow_html=True)
st.markdown("""
<div class="highlight-box">
    <p><strong>Informasi Rekomendasi Shift:</strong> Sistem menganalisis pola microsleep setiap pengemudi dan merekomendasikan shift optimal berdasarkan:</p>
    <ul>
        <li>Analisis waktu dengan microsleep terendah untuk setiap pengemudi</li>
        <li>Menjamin minimal pengemudi per shift sesuai kebutuhan operasional</li>
        <li>Prioritas perubahan untuk pengemudi berisiko tinggi</li>
        <li>Keseimbangan distribusi pengemudi antar shift</li>
    </ul>
</div>
""", unsafe_allow_html=True)

shift_counts = drivers_df['recommended_shift'].value_counts().reset_index()
shift_counts.columns = ['Shift', 'Jumlah Pengemudi']

col1, col2, col3 = st.columns(3)

with col1:
    pagi_count = shift_counts[shift_counts['Shift'] == 'Shift Pagi']['Jumlah Pengemudi'].values[0] if 'Shift Pagi' in shift_counts['Shift'].values else 0
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #4CAF50;'>
        <h3>Shift Pagi (06:00-14:00)</h3>
        <h2 style='color: #4CAF50; font-size: 2.5rem;'>{pagi_count}</h2>
        <p>Pengemudi direkomendasikan</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    siang_count = shift_counts[shift_counts['Shift'] == 'Shift Siang']['Jumlah Pengemudi'].values[0] if 'Shift Siang' in shift_counts['Shift'].values else 0
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #FFC107;'>
        <h3>Shift Siang (14:00-22:00)</h3>
        <h2 style='color: #FFC107; font-size: 2.5rem;'>{siang_count}</h2>
        <p>Pengemudi direkomendasikan</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    malam_count = shift_counts[shift_counts['Shift'] == 'Shift Malam']['Jumlah Pengemudi'].values[0] if 'Shift Malam' in shift_counts['Shift'].values else 0
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #3F51B5;'>
        <h3>Shift Malam (22:00-06:00)</h3>
        <h2 style='color: #3F51B5; font-size: 2.5rem;'>{malam_count}</h2>
        <p>Pengemudi direkomendasikan</p>
    </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<h3 class='section-title'>🧑‍✈️ Rekomendasi Shift Per Pengemudi</h3>", unsafe_allow_html=True)

st.markdown("<div class='table-container'>", unsafe_allow_html=True)
filter_options = st.multiselect("Filter berdasarkan Tingkat Risiko:", 
                               options=['Rendah', 'Sedang', 'Tinggi'], 
                               default=['Rendah', 'Sedang', 'Tinggi'])

filtered_drivers = drivers_df[drivers_df['risk_level'].isin(filter_options)]

if not filtered_drivers.empty:
    display_df = filtered_drivers[['nama_sopir', 'risk_level', 'microsleep_events', 'current_primary_shift', 'recommended_shift']].copy()
    display_df = display_df.sort_values(['risk_level', 'microsleep_events'], 
                                       key=lambda x: x.map({'Rendah': 0, 'Sedang': 1, 'Tinggi': 2}) if x.name == 'risk_level' else x)
    
    def format_risk_level(risk):
        css_class = 'low-risk' if risk == 'Rendah' else 'med-risk' if risk == 'Sedang' else 'high-risk'
        return f'<span class="alert-level {css_class}">{risk}</span>'
    
    def format_shift(shift):
        shift_type = shift.split(' ')[1].lower() if ' ' in shift else 'pagi'
        return f'<span class="shift-pill {shift_type}-shift">{shift}</span>'
    
    display_html_df = display_df.copy()
    display_html_df['risk_level'] = display_html_df['risk_level'].apply(format_risk_level)
    display_html_df['current_primary_shift'] = display_html_df['current_primary_shift'].apply(format_shift)
    display_html_df['recommended_shift'] = display_html_df['recommended_shift'].apply(format_shift)
    
    display_html_df.columns = ['Nama Pengemudi', 'Tingkat Risiko', 'Jumlah Microsleep', 'Shift Saat Ini', 'Shift Direkomendasikan']
    
    st.write(display_html_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Unduh Rekomendasi Shift (CSV)",
        data=csv,
        file_name=f"rekomendasi_shift_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv",
        mime='text/csv',
    )
else:
    st.info("Tidak ada data pengemudi yang sesuai dengan filter yang dipilih.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<h3 class='section-title'>🔄 Analisis Perubahan Shift</h3>", unsafe_allow_html=True)

st.markdown("<div class='info-container'>", unsafe_allow_html=True)
shift_changes = drivers_df[drivers_df['current_primary_shift'] != drivers_df['recommended_shift']]
total_changes = len(shift_changes)
percent_changes = (total_changes / len(drivers_df)) * 100 if len(drivers_df) > 0 else 0

risk_level_changes = shift_changes['risk_level'].value_counts()
high_risk_changes = risk_level_changes.get('Tinggi', 0)
med_risk_changes = risk_level_changes.get('Sedang', 0)
low_risk_changes = risk_level_changes.get('Rendah', 0)

st.markdown(f"""
<p>Rekomendasi menghasilkan <strong>{total_changes} perubahan shift</strong> ({percent_changes:.1f}% dari total pengemudi), dengan perubahan terbanyak pada:</p>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #F44336;'>
        <h3>Perubahan Risiko Tinggi</h3>
        <h2 style='color: #F44336; font-size: 2.5rem;'>{high_risk_changes}</h2>
        <p>Pengemudi dengan risiko tinggi</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #FFC107;'>
        <h3>Perubahan Risiko Sedang</h3>
        <h2 style='color: #FFC107; font-size: 2.5rem;'>{med_risk_changes}</h2>
        <p>Pengemudi dengan risiko sedang</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='stats-card' style='border-top: 5px solid #4CAF50;'>
        <h3>Perubahan Risiko Rendah</h3>
        <h2 style='color: #4CAF50; font-size: 2.5rem;'>{low_risk_changes}</h2>
        <p>Pengemudi dengan risiko rendah</p>
    </div>
    """, unsafe_allow_html=True)

if not shift_changes.empty:
    st.markdown("<div class='spacer'></div>", unsafe_allow_html=True)
    st.markdown("<strong>Detail Perubahan Shift:</strong>", unsafe_allow_html=True)
    
    display_changes = shift_changes[['nama_sopir', 'risk_level', 'microsleep_events', 'current_primary_shift', 'recommended_shift']].copy()
    display_changes = display_changes.sort_values('risk_level', key=lambda x: x.map({'Tinggi': 0, 'Sedang': 1, 'Rendah': 2}))
    
    display_html_changes = display_changes.copy()
    display_html_changes['risk_level'] = display_html_changes['risk_level'].apply(format_risk_level)
    display_html_changes['current_primary_shift'] = display_html_changes['current_primary_shift'].apply(format_shift)
    display_html_changes['recommended_shift'] = display_html_changes['recommended_shift'].apply(format_shift)
    
    display_html_changes.columns = ['Nama Pengemudi', 'Tingkat Risiko', 'Jumlah Microsleep', 'Shift Saat Ini', 'Shift Direkomendasikan']
    
    st.write(display_html_changes.to_html(escape=False, index=False), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)