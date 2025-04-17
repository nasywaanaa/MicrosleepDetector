# mongodb_connection.py
import pymongo
import streamlit as st

# Retrieve the MongoDB URI from Streamlit secrets
MONGO_URI = st.secrets["MONGO_URI"]

def get_mongo_client():
    if MONGO_URI is None:
        raise ValueError("MONGO_URI is not set in Streamlit secrets")
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
