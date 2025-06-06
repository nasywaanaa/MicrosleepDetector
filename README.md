# SIGAP: Sistem Intelijen Gerak dan Aktivitas Pengemudi

SIGAP adalah sistem pendeteksi microsleep berbasis IoT dan AI yang dirancang untuk meningkatkan keselamatan pengemudi, terutama untuk angkutan barang dan transportasi jarak jauh. Sistem ini menggunakan teknologi computer vision dan machine learning untuk mendeteksi tanda-tanda kantuk pada pengemudi melalui analisis Eye Aspect Ratio (EAR).

## Latar Belakang

Berdasarkan data Korlantas Polri, tercatat 103.645 kecelakaan lalu lintas di Indonesia pada tahun 2021, meningkat 3,6% dari tahun sebelumnya. Menurut Komite Nasional Keselamatan Transportasi (KNKT), 80% kecelakaan disebabkan oleh faktor kelelahan pengemudi yang menyebabkan microsleep.

## Struktur Project

```
├── ai/                           # Modul-modul AI dan pemrosesan gambar
│   ├── _pycache_/                # Direktori Python cache
│   ├── data/                     # Data untuk pelatihan dan pengujian
│   ├── models/                   # Model machine learning terlatih
│   ├── utils/                    # Utility functions untuk AI
│   ├── venv/                     # Virtual environment Python
│   ├── .env                      # Environment variables untuk modul AI
│   ├── eye_analyzer.py           # Modul analisis mata (perhitungan EAR)
│   ├── facemesh_module.py        # Implementasi MediaPipe Facemesh
│   ├── microsleep_detector.py      # Algoritma utama deteksi microsleep
│   ├── run_realtime_detecttion.py    # Script untuk menjalankan deteksi real-time
│   └── test_buzzer.py            # Script pengujian buzzer
│
├── assets/                       # Aset seperti gambar dan ikon
│
├── backend/                      # Modul backend untuk server dan API
│   ├── database/                 # Modul database
│   │   ├── db.py                 # Koneksi dan operasi database
│   │   ├── information.py        # Model informasi pengemudi
│   │   └── models.py             # Definisi skema database
│   ├── endpoints/                # Endpoint API REST
│   ├── model/                    # Model untuk backend
│   ├── utils/                    # Utility functions untuk backend
│   ├── .env                      # Environment variables untuk backend
│   ├── app.py                    # Aplikasi server utama
│   ├── cam.py                    # Modul integrasi kamera
│   └── index.js                  # Script JavaScript untuk frontend
│
├── doc/                          # Dokumentasi project
│
└── iot_device/                   # Kode untuk perangkat IoT
    ├── buzzer_control.h          # Header untuk kontrol buzzer
    ├── camera_config.h           # Konfigurasi kamera ESP32-CAM
    ├── http_client.cpp           # Implementasi HTTP client
    ├── main.ino                  # Program utama Arduino untuk ESP32
    └── streamlit_dashboard/      # Dashboard Streamlit untuk visualisasi data
```

## Cara Kerja Sistem

- Ketika sistem dinyalakan, ESP32-CAM langsung bekerja menangkap gambar wajah pengemudi dengan kecepatan 15-30 frame per detik. Gambar ini diproses oleh algoritma deteksi wajah untuk menemukan area mata.
- Saat sistem menemukan wajah, 68 titik landmark diidentifikasi secara real-time. Sistem secara khusus fokus pada titik 36-47 yang membentuk kontur mata kanan dan kiri.
- Dari titik-titik ini, sistem menghitung Eye Aspect Ratio (EAR) menggunakan formula matematis. Pada 50 frame pertama, sistem mengumpulkan data EAR normal dari pengemudi tersebut.
- Sistem menggunakan adaptive threshold, tidak menggunakan nilai baku yang sama untuk semua orang, melainkan mempelajari pola mata normal setiap pengemudi dan menetapkan nilai threshold yang personal.
- Ketika pengemudi mulai mengantuk, nilai EAR menurun secara bertahap. Jika nilai EAR turun 25% dari baseline personal selama lebih dari 3 detik berturut-turut, kondisi microsleep terdeteksi.
- Saat microsleep terdeteksi, ESP32 mengirim sinyal ke Buzzer, menghasilkan alarm. Data kejadian microsleep juga dikirim ke server cloud melalui HTTP POST request. Jika koneksi internet terputus, data disimpan sementara di MicroSD card.
- Di backend, data diproses dan divisualisasikan dalam dashboard yang komprehensif. Manajer transportasi dapat melihat pola microsleep setiap pengemudi, waktu-waktu kritis, dan mengidentifikasi faktor risiko.
- Analisis rekomendasi dengan menggunakan machine learning untuk penentuan shift pengemudi sudah diletakkan didalam file ./streamlit_dashboard/pages/🔄_Rekomendasi_Shift.py. Model yang digunakan dalam penentuan rekomendasi adalah dengan menggunakan KNN. Penentuan rekomendasi ini berdasarkan fitur tingkat risiko dari histori microsleep yang terjadi pada pengemudi dan intensitas microsleep yang terjadi. Namun, untuk memastikan kelancaran pembagian shift, maka ditempatkan minimal 1 pengemudi dengan kejadian microsleep terendah pada setiap shift. 

## Komponen Utama

### Hardware
- ESP 32 Cam : untuk menangkap gambar wajah pengemudi secara real-time.
- Jaringan Internet / Wi-Fi Module: untuk mengirimkan data ke server atau platform manajemen fleet.
- Buzzer: untuk memberikan peringatan suara kepada pengemudi ketika terdeteksi mengantuk.
- Power Supply : sebagai sumber daya sistem untuk beroperasi
- Kaber USB : sebagai connector ke power suply
- Breadboard : sebagai penyangga untuk penyusunan prototype

### Software
- **AI Modules**:
  - `eye_analyzer.py`: Mengimplementasikan perhitungan Eye Aspect Ratio
  - `facemesh_module.py`: Menggunakan MediaPipe Facemesh untuk deteksi titik wajah
  - `microsleep_detect.py`: Algoritma core untuk mendeteksi microsleep

- **Backend**:
  - `app.py`: Server utama Flask/FastAPI untuk menerima data
  - `db.py`: Manajemen database untuk menyimpan data 
  - `cam.py`: Integrasi dengan kamera untuk pengujian server-side

- **IoT Device**:
  - `main.ino`: Program utama untuk ESP32-CAM
  - `buzzer_control.h`: Kontrol buzzer dengan berbagai pola suara
  - `http_client.cpp`: Komunikasi dengan backend via HTTP

## Requirements

### Hardware
- ESP32-CAM
- Buzzer 5V
- Jaringan Internet / Wi-Fi Module
- Power Supply
- Kaber USB
- Breadboard

### Software
- Python 3.8+
- TensorFlow/TensorFlow Lite
- OpenCV
- MediaPipe
- Flask/FastAPI
- Streamlit
- Arduino IDE (untuk programming ESP32)

## Instalasi

### Backend dan AI Modules

1. Clone repository ini:
```bash
https://github.com/nasywaanaa/MicrosleepDetector.git
cd microsleepdetector
```

2. Siapkan virtual environment:
```bash
cd ai
python -m venv venv
source venv/bin/activate  # Di Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_realtime_detection.py
```

3. Setup backend:
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # Di Windows: venv\Scripts\activate
```

4. Jalankan server backend:
```bash
python app.py
```

### ESP32-CAM

1. Buka folder iot_device di Arduino IDE
2. Pilih board ESP32 Camera di Tools > Board
3. Sesuaikan konfigurasi di camera_config.h dan koneksi WiFi
4. Upload ke perangkat ESP32-CAM

## Penggunaan

1. Pasang ESP32-CAM dengan modul IR LED pada dashboard kendaraan
2. Pastikan ESP32-CAM memiliki akses ke internet (melalui tethering atau dedicated WiFi)
3. Mulai sistem dengan menyalakan power supply
4. Buka dashboard Streamlit untuk melihat data: 
```bash
https://microsleep-detector.streamlit.app/
```
5. Untuk login ke app gunakan akun berikut:

    Username: admin

    Password: sigap123

## Performa

Berdasarkan pengujian, sistem ini mencapai:
- Akurasi deteksi microsleep: 97% (kondisi pencahayaan normal)
- Akurasi dengan pengemudi berkacamata: 93%
- Waktu respons rata-rata: < 500ms

## Kontributor

- [Marzuli Suhada M](https://github.com/zultopia) - AI Engineer
- [Nasywaa Anggun Athiefah](https://github.com/nasywaanaa) - AI Engineer
- [Ahmad Mudabbir Arif](https://github.com/Dabbir) - IoT Developer
- [Jihan Aurelia](https://github.com/jijiau) - IoT Developer

## Lisensi

Proyek ini dilisensikan di bawah MIT License - lihat file [LICENSE](LICENSE) untuk detail.

## Acknowledgements

- [OpenCV](https://opencv.org/) - Computer Vision Library
- [MediaPipe](https://mediapipe.dev/) - Framework untuk Face Mesh
- [TensorFlow](https://www.tensorflow.org/) - Machine Learning Framework
- [C. Dewi et al.](https://doi.org/10.3390/electronics11193183) - Paper "Eye Aspect Ratio for Real-Time Drowsiness Detection"