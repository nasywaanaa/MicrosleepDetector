import serial
import time
import msvcrt  # Windows-specific module for keyboard input

# Ganti dengan port kamu
# port = '/dev/tty.SLAB_USBtoUART'  # Mac
port = 'COM3'  # Windows

try:
    ser = serial.Serial(port, 9600, timeout=1)
    time.sleep(2)  # Waktu tunggu koneksi serial stabil
    
    print("Press SPACE to trigger buzzer. Press Ctrl+C to exit.")
    
    while True:
        try:
            if msvcrt.kbhit():  # Check if a key is pressed
                key = msvcrt.getch()  # Get the pressed key
                if key == b' ':  # Space key
                    ser.write(b'B')
                    print("📢 Sent 'B' to ESP32 to trigger buzzer.")
        except KeyboardInterrupt:
            print("\n🛑 Program terminated by user.")
            break
        time.sleep(0.1)  # Short delay to reduce CPU usage
        
except Exception as e:
    print(f"❌ Failed: {e}")
finally:
    # Make sure to close the serial connection when exiting
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial connection closed.")
