from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load credentials from .env file (if used)
load_dotenv()

# Ganti dengan connection string kamu sendiri
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("MONGO_DB_NAME", "MicrosleepDetector")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "information")

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]

    # Hapus semua dokumen di collection
    result = collection.delete_many({})
    print(f"✅ Berhasil menghapus {result.deleted_count} dokumen dari koleksi '{COLLECTION_NAME}'.")

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
