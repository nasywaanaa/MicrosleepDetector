import pymongo
import streamlit as st

# Load kredensial dari secrets
sec = st.secrets["secrets"]

def get_mongo_client():
    MONGO_URI = sec["MONGO_URI"]
    
    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in secrets")
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
