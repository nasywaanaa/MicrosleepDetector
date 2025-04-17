# mongodb_connection.py

import pymongo
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the MongoDB URI from the environment
MONGO_URI = os.getenv("MONGO_URI")

def get_mongo_client():
    if MONGO_URI is None:
        raise ValueError("MONGO_URI is not set in the environment variables")
    
    # Set up the MongoDB connection
    client = pymongo.MongoClient(MONGO_URI)
    db = client["MicrosleepDetector"]
    collection = db["information"]
    return collection
