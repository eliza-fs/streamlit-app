# actions.py
import time # Utk waktu cooldown notif
import requests # Utk membuat HTTP request
import pygame # Utk pengembangan game, tp di sini digunakan modul mixernya utk memainkan suara
import os # Lib utk berinteraksi dgn sistem operasi (utk mengecek keberadaan file)

# --- Konfigurasi Alarm Suara ---
ALARM_SOUND_FILE = "alarm.mp3" 

def play_alarm():
    """Memainkan suara alarm jika belum dimainkan."""
    try:
        if not pygame.mixer.get_init(): # Inisialisasi pygame mixer hanya sekali di awal
            pygame.mixer.init()
        
        # Cek apakah suara sedang dimainkan
        if not pygame.mixer.music.get_busy(): # get_busy() me-return True jk suara sdg diputar (mencegah alarm diputar scr tabrakan)
            if os.path.exists(ALARM_SOUND_FILE): # Cek apkh file suara bnr" ada di folder
                pygame.mixer.music.load(ALARM_SOUND_FILE)
                pygame.mixer.music.play() # Memainkan suara sekali 
                print("ALARM: Playing alarm sound!")
            else:
                print(f"ALARM: Sound file not found at {ALARM_SOUND_FILE}")
    except Exception as e:
        print(f"Error playing alarm: {e}")

# --- Konfigurasi Telegram ---
# Variabel untuk mencegah spam Telegram
last_telegram_time = 0
TELEGRAM_COOLDOWN_SECONDS = 60 # Kirim Telegram sekali per 60 detik

def send_telegram_alert():
    """Mengirim pesan peringatan ke Telegram."""
    global last_telegram_time # Utk memodifikasi  variabel di luar fungsi ini
    
    current_time = time.time() # Dapatkan waktu saat ini
    if current_time - last_telegram_time < TELEGRAM_COOLDOWN_SECONDS:
        print(f"TELEGRAM: Cooldown active. Not sending message.")
        return # Keluar dari fungsi jika masih ada cooldown

    try:
        # Data yg didapatkan dari bot telegram
        bot_token = "8523118569:AAHyOp8JlqWap-POyK5iRkoW4TIySqnw_aQ" # <--- GANTI INI
        chat_id = "1736288934" # <--- GANTI INI
        
        message_body = "⚠️ PERINGATAN: SnapDriver mendeteksi pengemudi mengantuk berulang kali. Mohon segera hubungi atau pastikan pengemudi dalam kondisi aman!"

        # URL untuk Telegram Bot API
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # Data yang akan dikirim
        payload = {
            'chat_id': chat_id,
            'text': message_body,
            'parse_mode': 'HTML' # Memungkinkan penggunaan tag HTML sederhana di pesan
        }

        # Lakukan request POST ke server Telegram dgn data yg sdh disiapkan
        response = requests.post(url, json=payload)

        # Cek apakah pesan terkirim
        if response.status_code == 200:
            print("TELEGRAM: Alert sent successfully!")
            last_telegram_time = current_time
        else:
            print(f"TELEGRAM: Failed to send alert. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error sending Telegram alert: {e}")