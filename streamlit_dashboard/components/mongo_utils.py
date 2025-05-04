import pandas as pd
import streamlit as st
from mongodb_connection import get_mongo_client
from components.generate_data import generate_data

def fetch_data_from_mongo(include_data=True):
    try:
        collection = get_mongo_client()
        query = {}
        projection = {"_id": 0}
        cursor = collection.find(query, projection)
        data = pd.DataFrame(list(cursor))
        
        if 'timestamp' not in data.columns:
            st.error("Error: 'timestamp' column not found in the MongoDB collection!")
            return pd.DataFrame()
        
        data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')
        
        if data['timestamp'].isnull().any():
            st.warning("Some 'timestamp' values could not be converted properly.")
        
        # if include_data:
        #     data_df = generate_data(n=300)
        #     data = pd.concat([data, data_df], ignore_index=True)

        return data

    except Exception as e:
        st.error(f"MongoDB Fetch Error: {e}")
        return pd.DataFrame()
