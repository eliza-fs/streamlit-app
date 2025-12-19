# model_loader.py
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models, regularizers
import os

# --- KONFIGURASI MODEL ---
SEQ_LEN = 16
IMG_SIZE = 96
CLASSES = ["Yawning", "Talking", "Yawning & Talking", "Normal"]

def load_trained_model(model_path="snapdriver_model.h5"):
    """
    Fungsi untuk memuat model yang sudah dilatih dengan cara yang lebih toleran.
    """
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return None

    try:
        print("Recreating model architecture...")
        
        # 1. Bangun kembali arsitektur model yang sama persis seperti saat training
        cnn_base = MobileNetV2(weights='imagenet', include_top=False, input_shape=(IMG_SIZE, IMG_SIZE, 3))
        cnn_base.trainable = True

        input_layer = layers.Input(shape=(SEQ_LEN, IMG_SIZE, IMG_SIZE, 3))
        x = layers.TimeDistributed(cnn_base)(input_layer)
        x = layers.TimeDistributed(layers.GlobalAveragePooling2D())(x)
        x = layers.LSTM(32, dropout=0.3)(x)
        x = layers.Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.0001))(x)
        x = layers.Dropout(0.3)(x)
        output_layer = layers.Dense(len(CLASSES), activation='softmax')(x)

        model = models.Model(inputs=input_layer, outputs=output_layer)

        # 2. Muat bobot dengan cara yang toleran
        # by_name=True: hanya muat bobot untuk layer dengan nama yang sama
        # skip_mismatch=True: lewati layer yang bentuk bobotnya tidak cocok
        model.load_weights(model_path, by_name=True, skip_mismatch=True)
        
        print("Model weights loaded successfully (some layers might have been skipped).")
        return model
    except Exception as e:
        print(f"Error loading model weights: {e}")
        return None