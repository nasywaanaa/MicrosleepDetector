import pymongo
import streamlit as st
import os

MONGO_URI = st.secrets.get("MONGO_URI", os.getenv("MONGO_URI", None))

def get_mongo_client():
    if not MONGO_URI:
        raise ValueError("MONGO_URI is not set in secrets or environment variables.")
    
    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
