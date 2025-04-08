from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

UBIDOTS_TOKEN = "BBUS-yMUTCmpUek2MH1Aezcxi9pcfcehJBA"  # Ganti dengan token kamu
DEVICE_LABEL = "esp32-cam" # Ganti dengan label device kamu

@app.route("/vision", methods=["POST"])
def receive_vision_data():
    data = request.json
    print("Received data:", data)

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

    return jsonify({
        "status": "success",
        "ubidots_response": response.json()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
