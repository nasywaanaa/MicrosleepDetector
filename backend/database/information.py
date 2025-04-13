from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(
    mongo_uri,
    tls=True,
    tlsAllowInvalidCertificates=True  # ← aktifkan untuk development
)

print("MONGO URI:", mongo_uri)
print("Client config OK")


db = client["MicrosleepDetector"]
collection = db["information"]

data_dummy = [
    {
        "nama_sopir": "Budi Santoso",
        "timestamp": datetime(2025, 4, 13, 14, 30),
        "armada": "B1234XYZ",
        "rute": "Jakarta - Bandung",
        "status_alert": "Mengantuk"
    }
]

result = collection.insert_many(data_dummy)
print(f"{len(result.inserted_ids)} data berhasil dimasukkan.")
