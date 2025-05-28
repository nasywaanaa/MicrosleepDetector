# import certifi
from flask import Flask, request, jsonify
import requests
from pymongo import MongoClient
import datetime
from datetime import datetime, timezone

from dotenv import load_dotenv
import os

load_dotenv()  # Baca file .env

app = Flask(__name__)

# UBIDOTS setup
UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")
DEVICE_LABEL = "esp32-cam"

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True  # ← aktifkan untuk development
)
db = client["MicrosleepDetector"]
collection = db["information"]

@app.route("/vision", methods=["POST"])
def receive_vision_data():
    try:
        data = request.json
        print("Received data:", data)

        document = {
            "nama_sopir": data.get("nama_sopir", "Unknown"),
            "timestamp": datetime.fromisoformat(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
            "armada": data.get("armada", "Unknown"),
            "rute": data.get("rute", "Unknown"),
            "status_alert": data.get("status_alert", "NORMAL"),
        }

        result = collection.insert_one(document)
        print("Inserted to MongoDB with ID:", result.inserted_id)

        ubidots_payload = {
            "driver_name": data.get("nama_sopir", "Unknown"),
            "armada": data.get("armada", "Unknown"),
            "rute": data.get("rute", "Unknown"),
            "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "status_alert": 1 if data.get("status_alert") == "MICROSLEEP" else 0
        }

        headers = {
            "X-Auth-Token": UBIDOTS_TOKEN,
            "Content-Type": "application/json"
        }

        url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
        response = requests.post(url, headers=headers, json=ubidots_payload)
        print("Ubidots response:", response.status_code)

        return jsonify({
            "status": "success",
            "ubidots_response": response.json() if response.status_code == 200 else {"error": response.status_code}
        })
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
