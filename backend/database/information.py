from flask import Flask, jsonify, request  # Perbaikan impor Flask
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from pathlib import Path

import requests

# Inisialisasi Flask
app = Flask(__name__)  # Tambahkan inisialisasi app

# Konfigurasi environment
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=env_path)

# Ubidots configuration
UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")
DEVICE_LABEL = os.getenv("DEVICE_LABEL", "esp32-cam")  # Tambahkan definisi DEVICE_LABEL

# MongoDB configuration
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

# Cek apakah perlu mengisi data dummy (hanya jika collection kosong)
# if collection.count_documents({}) == 0:
#     data_dummy = [
#         {
#             "nama_sopir": "Budi Santoso",
#             "timestamp": datetime(2025, 4, 13, 14, 30),
#             "armada": "B1234XYZ",
#             "rute": "Jakarta - Bandung",
#             "status_alert": "Mengantuk"
#         }
#     ]
#     result = collection.insert_many(data_dummy)
#     print(f"{len(result.inserted_ids)} data dummy berhasil dimasukkan.")

@app.route("/vision", methods=["POST"])
def receive_vision_data():
    try:
        data = request.json
        print("Received data:", data)

        # Sesuaikan struktur dokumen dengan collection information
        document = {
            "nama_sopir": data.get("nama_sopir", "Unknown"),
            "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            "armada": data.get("armada", "Unknown"),
            "rute": data.get("rute", "Unknown"),
            "status_alert": data.get("status_alert", "OFF"),
        }

        result = collection.insert_one(document)
        print("Inserted to MongoDB with ID:", result.inserted_id)

        # Jika UBIDOTS_TOKEN tersedia, kirim data ke Ubidots
        if UBIDOTS_TOKEN:
            ubidots_payload = {
                "driver_name": data.get("nama_sopir", "Unknown"),
                "armada": data.get("armada", "Unknown"),
                "rute": data.get("rute", "Unknown"),
                "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "status_alert": 1 if data.get("status_alert") == "ON" else 0
            }

            headers = {
                "X-Auth-Token": UBIDOTS_TOKEN,
                "Content-Type": "application/json"
            }

            try:
                url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
                response = requests.post(url, headers=headers, json=ubidots_payload, timeout=3)
                print("Ubidots response:", response.status_code)
                ubidots_response = response.json() if response.status_code == 200 else {"error": response.status_code}
            except requests.exceptions.RequestException as e:
                print("Ubidots connection error:", e)
                ubidots_response = {"error": str(e)}
        else:
            ubidots_response = {"message": "UBIDOTS_TOKEN not configured"}

        return jsonify({
            "status": "success",
            "mongodb_id": str(result.inserted_id),
            "ubidots_response": ubidots_response if UBIDOTS_TOKEN else {"message": "Ubidots integration disabled"}
        })
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def status():
    """Endpoint untuk memeriksa status server"""
    try:
        # Coba mengambil 1 document dari MongoDB untuk memverifikasi koneksi
        document = collection.find_one({}, {"_id": 1})
        
        return jsonify({
            "status": "online",
            "mongodb_connection": "OK" if document else "Connected but empty collection",
            "database": db.name,
            "collection": collection.name,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "online",
            "mongodb_connection": "ERROR",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/data", methods=["GET"])
def get_recent_data():
    """Endpoint untuk mendapatkan data terbaru"""
    try:
        # Ambil 10 data terbaru berdasarkan timestamp
        recent_data = list(collection.find({}, {
            "_id": 0,
            "nama_sopir": 1, 
            "timestamp": 1, 
            "armada": 1, 
            "rute": 1, 
            "status_alert": 1
        }).sort("timestamp", -1).limit(10))
        
        # Convert datetime objects to strings
        for item in recent_data:
            if "timestamp" in item and isinstance(item["timestamp"], datetime):
                item["timestamp"] = item["timestamp"].isoformat()
        
        return jsonify(recent_data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Tambahkan rute root untuk debugging
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "status": "running",
        "message": "Microsleep Detector API is running",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "This information"},
            {"path": "/vision", "method": "POST", "description": "Send microsleep detection data"},
            {"path": "/status", "method": "GET", "description": "Check server status"},
            {"path": "/data", "method": "GET", "description": "Get recent data"}
        ],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("Starting Microsleep Detector Server on port 5000...")
    print(f"Database: {db.name}, Collection: {collection.name}")
    app.run(host="0.0.0.0", port=5000, debug=True)  # Tambahkan debug=True untuk melihat error