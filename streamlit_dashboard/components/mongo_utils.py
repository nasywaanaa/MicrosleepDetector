import pandas as pd
import streamlit as st
import pymongo
import certifi
from components.generate_data import generate_data

def fetch_data_from_mongo():
    """
    Fetch microsleep data from MongoDB, or generate dummy data if connection fails
    
    Returns:
    --------
    pd.DataFrame
        DataFrame containing microsleep data
    """
    try:
        if "secrets" in st.secrets and "MONGO_URI" in st.secrets["secrets"]:
            mongo_uri = st.secrets["secrets"]["MONGO_URI"]

            client = pymongo.MongoClient(
                mongo_uri, 
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000 
            )
            
            client.admin.command('ping')
            
            db = client["MicrosleepDetector"]
            collection = db["information"]
            
            query = {}
            projection = {"_id": 0} 
            cursor = collection.find(query, projection)
            
            data = pd.DataFrame(list(cursor))
            
            if data.empty:
                st.warning("Tidak ada data di MongoDB. Menggunakan data dummy.")
                return generate_dummy_data()
            
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
                
                if data['timestamp'].isnull().any():
                    st.warning("Beberapa nilai timestamp tidak valid. Data mungkin tidak lengkap.")
                
                return data
            else:
                st.warning("Format data tidak valid. Menggunakan data dummy.")
                return generate_dummy_data()
                
        else:
            st.warning("MONGO_URI tidak ditemukan di secrets. Menggunakan data dummy.")
            return generate_dummy_data()
            
    except Exception as e:
        st.error(f"MongoDB Fetch Error: {e}")
        st.info("Menggunakan data dummy sebagai pengganti.")
        return generate_dummy_data()

def generate_dummy_data():
    """
    Generate dummy data for development and testing
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with dummy microsleep data
    """
    dummy_data = generate_data(n=300)
    
    return dummy_data