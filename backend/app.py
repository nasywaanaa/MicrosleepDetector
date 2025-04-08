import certifi
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
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["microsleep_db"]  # Nama database
collection = db["vision_logs"]  # Nama koleksi/tabel

@app.route("/vision", methods=["POST"])
def receive_vision_data():
    try:
        data = request.json
        print("Received data:", data)

        document = {
            "face_count": data.get("face_count", 0),
            "eye_count": data.get("eye_count", 0),
            "timestamp": datetime.now(timezone.utc)
        }

        result = collection.insert_one(document)
        print("Inserted to MongoDB with ID:", result.inserted_id)

        ubidots_payload = {
            "face_count": data.get("face_count", 0),
            "eye_count": data.get("eye_count", 0)
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
            "ubidots_response": response.json()
        })
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
