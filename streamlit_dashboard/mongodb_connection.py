import pymongo
import streamlit as st
import os

def get_mongo_client():
    MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
    
    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in environment variables or Streamlit secrets")

    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
