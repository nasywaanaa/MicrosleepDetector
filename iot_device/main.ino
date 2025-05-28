#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define BUZZER_PIN 25
#define MAX_EVENTS 5         // Jumlah maksimal event yang direkam (diubah dari 10 menjadi 5)
#define TIME_WINDOW 60000    // Jendela waktu untuk melacak trigger (60 detik)

// Konfigurasi OLED
#define SCREEN_WIDTH 128     // Lebar OLED dalam piksel
#define SCREEN_HEIGHT 64     // Tinggi OLED dalam piksel
#define OLED_RESET -1        // Reset pin # (atau -1 jika berbagi reset Arduino)
#define SCREEN_ADDRESS 0x3C  // Alamat I2C OLED (biasanya 0x3C atau 0x3D)

// Parameter buzzer
#define MAX_FREQUENCY 2777   // Frekuensi maksimum (diubah dari 4000 menjadi 3000)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Array untuk menyimpan waktu trigger terjadi
unsigned long triggerTimes[MAX_EVENTS];
int triggerCount = 0;
int currentIndex = 0;

// Tingkat keparahan microsleep (tanpa level normal)
const char* alertLevels[] = {
  "WASPADA",
  "BAHAYA",
  "BERHENTI!"
};

// Warna untuk level - dalam format monokrom ini berarti pola pengisian
const uint8_t SOLID = 1;
const uint8_t HATCHED = 2;
const uint8_t INVERTED = 3;

// Animasi
unsigned long lastAnimationTime = 0;
bool animationState = false;
int animationSpeed = 500; // ms

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Inisialisasi array waktu trigger
  for (int i = 0; i < MAX_EVENTS; i++) {
    triggerTimes[i] = 0;
  }
  
  // Inisialisasi OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Loop forever jika gagal
  }
  
  // Tampilkan splash screen
  showSplashScreen();
  
  // Tampilkan status awal
  updateDisplay(0);
}

void loop() {
  // Update animasi jika diperlukan
  unsigned long currentTime = millis();
  if (currentTime - lastAnimationTime > animationSpeed) {
    animationState = !animationState;
    lastAnimationTime = currentTime;
    
    // Perbarui tampilan jika dalam status alert tinggi
    if (triggerCount > 0) {
      float intensityFactor = constrain(triggerCount / (float)MAX_EVENTS, 0, 1);
      updateDisplay(intensityFactor);
    }
  }
  
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'B') {
      // Rekam waktu trigger saat ini
      recordTrigger();
      
      // Hitung jumlah trigger dalam jendela waktu
      countRecentTriggers();
      
      // Update tampilan OLED
      float intensityFactor = constrain(triggerCount / (float)MAX_EVENTS, 0, 1);
      updateDisplay(intensityFactor);
      
      // Aktifkan buzzer dengan pola sesuai tingkat keparahan
      activateBuzzerPattern(triggerCount);
      
      // Setel kecepatan animasi berdasarkan tingkat keparahan
      animationSpeed = map(triggerCount, 1, MAX_EVENTS, 500, 150);
    }
  }
}

void showSplashScreen() {
  display.clearDisplay();
  
  // Logo atau judul
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(5, 5);
  display.println(F("MICROSLEEP"));
  
  // Subtitle
  display.setTextSize(1);
  display.setCursor(15, 25);
  display.println(F("Detection System"));
  
  // Versi 
  display.setCursor(40, 40);
  display.println(F("v2.0"));
  
  // Garis bawah
  display.drawLine(0, 50, SCREEN_WIDTH, 50, SSD1306_WHITE);
  
  // Initializing text
  display.setCursor(15, 55);
  display.println(F("Initializing..."));
  
  display.display();
  delay(2000);
}

void recordTrigger() {
  // Simpan waktu trigger saat ini
  triggerTimes[currentIndex] = millis();
  
  // Update index untuk trigger berikutnya
  currentIndex = (currentIndex + 1) % MAX_EVENTS;
}

void countRecentTriggers() {
  unsigned long currentTime = millis();
  triggerCount = 0;
  
  // Hitung jumlah trigger dalam jendela waktu
  for (int i = 0; i < MAX_EVENTS; i++) {
    if (triggerTimes[i] > 0 && currentTime - triggerTimes[i] < TIME_WINDOW) {
      triggerCount++;
    }
  }
  
  // Cetak jumlah trigger untuk debugging
  Serial.print("Jumlah trigger dalam 60 detik terakhir: ");
  Serial.println(triggerCount);
}

void activateBuzzerPattern(int count) {
  // Mengatur volume berdasarkan jumlah trigger
  // Semakin banyak trigger, semakin keras
  int volume = map(count, 1, MAX_EVENTS, 255, 1023);  // Asumsi menggunakan analogWrite
  
  // Durasi beep sesuai dengan tingkat
  int beepDuration = (count <= 2) ? 500 : 1000;
  
  // Jarak antara beep
  int pauseDuration = (count <= 3) ? 300 : map(count, 4, MAX_EVENTS, 250, 100);
  
  // Frekuensi dasar - menggunakan MAX_FREQUENCY yang baru (3000 Hz)
  int frequency = map(count, 1, MAX_EVENTS, 1000, MAX_FREQUENCY);
  
  Serial.print("Trigger count: ");
  Serial.print(count);
  Serial.print(", Volume: ");
  Serial.print(volume);
  Serial.print(", Frekuensi: ");
  Serial.print(frequency);
  Serial.print(" Hz, Durasi: ");
  Serial.print(beepDuration);
  Serial.print(" ms, Jeda: ");
  Serial.print(pauseDuration);
  Serial.println(" ms");
  
  // Pola beep berdasarkan level
  switch (count) {
    case 1:
      // Tingkat 1: satu beep panjang
      tone(BUZZER_PIN, frequency, beepDuration);
      break;
      
    case 2:
      // Tingkat 2: dua beep
      tone(BUZZER_PIN, frequency, beepDuration);
      delay(beepDuration + pauseDuration);
      tone(BUZZER_PIN, frequency, beepDuration);
      break;
      
    case 3:
      // Tingkat 3: tiga beep
      for (int i = 0; i < 3; i++) {
        tone(BUZZER_PIN, frequency, beepDuration);
        delay(beepDuration + pauseDuration);
      }
      break;
      
    default:
      // Tingkat 4+: beep yang semakin cepat (untuk count 4 dan 5)
      int repeats = min(count, 5);  // Maksimal 5 kali beep (disesuaikan dengan MAX_EVENTS)
      for (int i = 0; i < repeats; i++) {
        tone(BUZZER_PIN, frequency, beepDuration / 2);
        delay((beepDuration / 2) + pauseDuration);
      }
      break;
  }
}

void updateDisplay(float intensity) {
  display.clearDisplay();
  
  // Pilih level peringatan berdasarkan intensitas
  // Karena MAX_EVENTS = 5, kita perlu menyesuaikan tingkat level
  // Level 0: 1 trigger (1/5 = 0.2 intensitas)
  // Level 1: 2-3 trigger (0.4-0.6 intensitas)
  // Level 2: 4-5 trigger (0.8-1.0 intensitas)
  int level = min(2, (int)(intensity * 3));
  
  // Header dengan judul dan garis
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(2, 2);
  display.print(F("MICROSLEEP MONITOR"));
  display.drawLine(0, 12, SCREEN_WIDTH, 12, SSD1306_WHITE);
  
  // Menampilkan status dengan ukuran font yang besar
  display.setTextSize(2);
  
  // Animasi text berkedip untuk level tinggi
  if (level >= 2) {
    if (animationState) {
      display.setTextColor(SSD1306_BLACK, SSD1306_WHITE); // Text inversi
    } else {
      display.setTextColor(SSD1306_WHITE);
    }
  }
  
  // Pusat teks alert
  int16_t x1, y1;
  uint16_t w, h;
  display.getTextBounds(alertLevels[level], 0, 0, &x1, &y1, &w, &h);
  int x = (SCREEN_WIDTH - w) / 2;
  int y = 20;
  
  display.setCursor(x, y);
  display.println(alertLevels[level]);
  display.setTextColor(SSD1306_WHITE); // Reset warna text
  
  // Menampilkan informasi level dengan ikon
  display.setTextSize(1);
  display.setCursor(2, 40);
  display.print(F("Level: "));
  display.print(level + 1);
  display.print(F("/3"));
  
  // Menampilkan jumlah deteksi
  display.setCursor(2, 50);
  display.print(F("Deteksi: "));
  display.print(triggerCount);
  display.print(F("/"));
  display.print(MAX_EVENTS);
  
  // Gambar bar progresif untuk visualisasi intensitas
  drawProgressBar(intensity);
  
  // Gambar ikon sesuai level keparahan
  drawAlertIcon(level);
  
  display.display();
}

void drawProgressBar(float progress) {
  int barWidth = 100;
  int barHeight = 8;
  int barX = 14;
  int barY = SCREEN_HEIGHT - 10;
  
  // Bingkai bar
  display.drawRect(barX, barY, barWidth, barHeight, SSD1306_WHITE);
  
  // Isi bar berdasarkan intensitas
  int fillWidth = (int)(barWidth * progress);
  
  // Pola pengisian berdasarkan tingkat keparahan
  int level = min(2, (int)(progress * 3));
  
  if (level == 0) {
    // Level 1: Solid fill
    display.fillRect(barX, barY, fillWidth, barHeight, SSD1306_WHITE);
  } 
  else if (level == 1) {
    // Level 2: Pola berselang-seling
    display.fillRect(barX, barY, fillWidth, barHeight, SSD1306_WHITE);
    
    // Tambahkan pola garis
    for (int i = barX + 2; i < barX + fillWidth; i += 4) {
      display.drawLine(i, barY + 1, i, barY + barHeight - 2, SSD1306_BLACK);
    }
  } 
  else {
    // Level 3: Animasi berkedip
    if (animationState) {
      display.fillRect(barX, barY, fillWidth, barHeight, SSD1306_WHITE);
    } else {
      for (int i = barX; i < barX + fillWidth; i += 2) {
        display.drawLine(i, barY, i, barY + barHeight - 1, SSD1306_WHITE);
      }
    }
  }
}

void drawAlertIcon(int level) {
  // Posisi ikon di sudut kanan atas
  int iconX = SCREEN_WIDTH - 20;
  int iconY = 20;
  int iconSize = 16;
  
  switch (level) {
    case 0: // WASPADA
      // Gambar segitiga peringatan
      display.drawTriangle(
        iconX, iconY + iconSize,
        iconX + iconSize/2, iconY,
        iconX + iconSize, iconY + iconSize,
        SSD1306_WHITE);
      
      // Tambahkan tanda seru di tengah
      display.drawLine(
        iconX + iconSize/2, iconY + 3,
        iconX + iconSize/2, iconY + iconSize - 5,
        SSD1306_WHITE);
      
      display.drawPixel(iconX + iconSize/2, iconY + iconSize - 2, SSD1306_WHITE);
      break;
      
    case 1: // BAHAYA
      // Gambar ikon yang lebih dominan - segitiga terisi
      if (animationState) {
        display.fillTriangle(
          iconX, iconY + iconSize,
          iconX + iconSize/2, iconY,
          iconX + iconSize, iconY + iconSize,
          SSD1306_WHITE);
          
        // Tanda seru berwarna hitam
        display.drawLine(
          iconX + iconSize/2, iconY + 3,
          iconX + iconSize/2, iconY + iconSize - 5,
          SSD1306_BLACK);
        
        display.drawPixel(iconX + iconSize/2, iconY + iconSize - 2, SSD1306_BLACK);
      } else {
        display.drawTriangle(
          iconX, iconY + iconSize,
          iconX + iconSize/2, iconY,
          iconX + iconSize, iconY + iconSize,
          SSD1306_WHITE);
          
        // Tanda seru berwarna putih
        display.drawLine(
          iconX + iconSize/2, iconY + 3,
          iconX + iconSize/2, iconY + iconSize - 5,
          SSD1306_WHITE);
        
        display.drawPixel(iconX + iconSize/2, iconY + iconSize - 2, SSD1306_WHITE);
      }
      break;
      
    case 2: // BERHENTI
      // Animasi ikon yang berkedip - ikon stop 
      if (animationState) {
        display.fillRect(iconX, iconY, iconSize, iconSize, SSD1306_WHITE);
      } else {
        display.drawRect(iconX, iconY, iconSize, iconSize, SSD1306_WHITE);
        display.drawLine(iconX, iconY, iconX + iconSize, iconY + iconSize, SSD1306_WHITE);
        display.drawLine(iconX, iconY + iconSize, iconX + iconSize, iconY, SSD1306_WHITE);
      }
      break;
  }
}