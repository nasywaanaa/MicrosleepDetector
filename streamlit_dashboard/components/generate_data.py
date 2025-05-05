import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def generate_data(n=300):
    np.random.seed(42)
    sopir_list = ['Budi', 'Siti', 'Andi', 'Rina', 'Joko', 'Mega']
    armada_list = ['Bus-001', 'Bus-002', 'BUS-003']
    rute_list = ['Jakarta-Bandung', 'Jakarta-Bogor', 'Jakarta-Cikampek']
    shift_weights = [0.15, 0.35, 0.50]

    data = []
    for _ in range(n):
        nama_sopir = np.random.choice(sopir_list)
        shift = np.random.choice(['pagi', 'siang', 'malam'], p=shift_weights)
        base_hour = (
            np.random.randint(10, 12) if shift == 'pagi'
            else np.random.randint(18, 20) if shift == 'siang'
            else np.random.choice(list(range(0, 5)) + [23])
        )
        timestamp = (
            pd.Timestamp.today().normalize() - pd.Timedelta(days=np.random.randint(0, 3)) +
            pd.Timedelta(hours=base_hour, minutes=np.random.randint(0, 60))
        )
        armada = np.random.choice(armada_list)
        rute = np.random.choice(rute_list)
        status_alert = np.random.choice(["ON", "OFF"], p=[0.75, 0.25])
        data.append({
            "nama_sopir": nama_sopir,
            "timestamp": timestamp,
            "armada": armada,
            "rute": rute,
            "status_alert": status_alert
        })

    return pd.DataFrame(data)
