# drowsiness_detector.py
import cv2
import numpy as np
import time
from collections import deque

# Import dari file-file yang kita buat
from model_loader import load_trained_model, CLASSES, SEQ_LEN
from video_processor import preprocess_frame

class DrowsinessDetector: # Memanggil load_trained_model() untuk memuat model AI
    def __init__(self, model_path="snapdriver_model.h5", yawning_threshold=5):
        """
        Inisialisasi detektor. Memuat model dan menyiapkan variabel.
        """
        print("Initializing DrowsinessDetector...")
        self.model = load_trained_model(model_path) # Memuat model
        if self.model is None:
            raise Exception("Model could not be loaded.")

        # Inisialisasi variabel
        self.yawning_threshold = yawning_threshold # Digunakan dlm loop pemrosesan
        self.consecutive_yawns = 0 # Penghitung deteksi yawning berturut"
        self.frames_for_prediction = deque(maxlen=SEQ_LEN) # Antrian untuk menyimpan 16 frame terakhir
        self.prediction_history = deque(maxlen=5) # SMOOTING_WINDOW_SIZE = 5

        self.stable_status = "Normal" # Variabel utk menyimpan status dan confidence akhir yg stabil
        self.confidence = 0.0
        print("DrowsinessDetector initialized successfully.")

    def process_frame(self, frame): # Fungsi utama yang dipanggil berulang" oleh main_backend.py
        # Menerima satu frame dlm format BGR dari webcam
        """
        Memproses satu frame dan mengembalikan status terkini.
        Ini adalah fungsi utama yang akan dipanggil.
        """
        processed_frame = preprocess_frame(frame) # Memproses frame (resize, normalisasi, dll)
        self.frames_for_prediction.append(processed_frame) # Menambahkan frame yg sdh diproses ke antrian 'frames_for_prediction'

        # Jika antrian sdh berisi 16 frame, mulai prediksi
        if len(self.frames_for_prediction) == SEQ_LEN:
            sequence_for_model = np.expand_dims(np.array(self.frames_for_prediction), axis=0) # Bentuk (1, 16, 96, 96, 3)
            prediction = self.model.predict(sequence_for_model) # Prediksi dgn model CNN + LSTM
            
            predicted_class_index = np.argmax(prediction) # Ambil index kelas dgn prob tertinggi
            predicted_class_name = CLASSES[predicted_class_index] # Ambil nama kelas dr CLASSES berdasarkan indeks
            self.confidence = np.max(prediction) # Ambil nilai prob tertinggi sbg tingkat confidence
            
            # Logika smoothing
            self.prediction_history.append(predicted_class_name) # Tambahkan hasil prediksi ke antrian
            if len(self.prediction_history) == 5: # 5 adalah SMOOTHING_WINDOW_SIZE
                self.stable_status = max(set(self.prediction_history), key=self.prediction_history.count) 
                # Cari kelas yg paling sering muncul

            # Logika trigger
            # Jika status yg sdh stabil adl Yawning, tambah hitungan
            if self.stable_status == "Yawning":
                self.consecutive_yawns += 1
            else:
                if self.consecutive_yawns > 0: # Jika status berubah dari Yawning, reset hitungan
                    self.consecutive_yawns = 0

        return self.stable_status, self.confidence

    def process_video_file(self, video_path):
        """
        Memproses seluruh file video dan mengembalikan hasil prediksi per frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Cannot open video file {video_path}")
            return []

        results = []
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Panggil fungsi process_frame yg sama spt di atas
            status, confidence = self.process_frame(frame)
            # Simpan hasil prediksi ke dlm daftar
            results.append({"frame": frame_count, "status": status, "confidence": confidence})
            frame_count += 1
        
        cap.release()
        return results