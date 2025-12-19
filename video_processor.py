# video_processor.py
import cv2
import numpy as np

IMG_SIZE = 96
FACE_CASCADE_PATH = "haarcascade_frontalface_default.xml"

# Cek apakah file ada di awal
import os
if not os.path.exists(FACE_CASCADE_PATH):
    print(f"ERROR: Haarcascade file not found at {FACE_CASCADE_PATH}")
else:
    print(f"SUCCESS: Haarcascade file found at {FACE_CASCADE_PATH}")

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)

def preprocess_frame(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))


    if len(faces) > 0:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized_frame = cv2.resize(frame_rgb, (IMG_SIZE, IMG_SIZE))
        normalized_frame = resized_frame / 255.0
        return normalized_frame
    else:
        return np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.float32)