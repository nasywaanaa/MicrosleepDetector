import pymongo
import streamlit as st

def get_mongo_client():
    MONGO_URI = st.secrets["MONGO_URI"]
    
    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in secrets")
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
