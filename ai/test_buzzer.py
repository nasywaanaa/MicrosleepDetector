import serial
import time

# Ganti dengan port kamu
port = '/dev/tty.SLAB_USBtoUART'  # Mac
# port = 'COM4'  # Windows

try:
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # Waktu tunggu koneksi serial stabil
    ser.write(b'B')
    print("📢 Sent 'B' to ESP32 to trigger buzzer.")
    ser.close()
except Exception as e:
    print(f"❌ Failed to send: {e}")
