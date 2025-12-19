# Mengimpor library yang diperlukan
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import random
import plotly.express as px
import plotly.graph_objects as go

# --- MODIFIKASI BACKEND: Impor library dan file backend ---
import cv2
import numpy as np
from drowsiness_detector import DrowsinessDetector
from actions import play_alarm
# --- AKHIR MODIFIKASI BACKEND ---

# ==============================
# 1. PAGE CONFIG & STYLING
# ==============================
st.set_page_config(
    page_title="SnapDrive AI",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #FAFAFA; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stMetric"] {
        background-color: #262730; border: 1px solid #41444C; padding: 15px;
        border-radius: 10px; color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .alert-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; color: white; }
    .safe { background-color: #1B5E20; border-left: 5px solid #4CAF50; }
    .warning { background-color: #F57F17; border-left: 5px solid #FFD600; }
    .danger { background-color: #B71C1C; border-left: 5px solid #FF5252; }
    </style>
""", unsafe_allow_html=True)

# ==============================
# 2. SESSION STATE
# ==============================
# --- PERUBAHAN: Inisialisasi state untuk login ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
# --- AKHIR PERUBAHAN ---

if "riwayat" not in st.session_state:
    st.session_state.riwayat = []
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "score" not in st.session_state:
    st.session_state.score = 100

# --- MODIFIKASI BACKEND: Inisialisasi state untuk backend (tanpa threading) ---
if "detector" not in st.session_state:
    st.session_state.detector = None
if "cap" not in st.session_state:
    st.session_state.cap = None
if "current_frame" not in st.session_state:
    st.session_state.current_frame = None
if "current_status" not in st.session_state:
    st.session_state.current_status = "Normal"
# --- AKHIR MODIFIKASI BACKEND ---

# ==============================
# 3. HELPER FUNCTIONS
# ==============================
def create_gauge_chart(value):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value, domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Driver Alertness Score", 'font': {'size': 20, 'color': 'white'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#00CC96" if value > 70 else "#EF553B"}, 'bgcolor': "white",
            'borderwidth': 2, 'bordercolor': "gray",
            'steps': [{'range': [0, 40], 'color': '#5e0000'}, {'range': [40, 70], 'color': '#5e4e00'}, {'range': [70, 100], 'color': '#003817'}],
        }
    ))
    fig.update_layout(paper_bgcolor = "rgba(0,0,0,0)", font = {'color': "white"}, height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- FUNGSI LOGIN ---
def page_login():
    st.markdown("""
        <style>
        .login-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; }
        .login-box { background-color: #262730; padding: 2rem; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.5); text-align: center; width: 300px; }
        </style>
        """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3097/3097180.png", width=80)
        st.title("SnapDrive AI")
        st.caption("Please log in to continue")
        username = st.text_input("Username / Email", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        VALID_CREDENTIALS = { "admin": "admin123", "user@snapdrive.com": "snapdrive" }
        if st.button("Login", type="primary", use_container_width=True):
            if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Username atau password salah.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# 4. PAGES
# ==============================
def page_home():
    st.markdown("## 🚗 SnapDrive Dashboard")
    st.markdown("### AI-Based Driver Drowsiness Monitoring System")
    
    total = len(st.session_state.riwayat)
    menguap = len([r for r in st.session_state.riwayat if r["Kondisi"] == "Menguap"])
    normal = total - menguap
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🛡️ Safety Score", f"{st.session_state.score}%", delta_color="normal")
    col2.metric("📷 Total Scans", total)
    col3.metric("✅ Normal Events", normal)
    col4.metric("😴 Drowsiness Events", menguap, delta="-High Risk" if menguap > 5 else "Normal", delta_color="inverse")

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("📊 Analytics Overview")
        if total > 0:
            df = pd.DataFrame(st.session_state.riwayat)
            if "Score" in df.columns:
                fig_line = px.line(df.reset_index(), x=df.index, y="Score", title="Alertness Score Over Time", markers=True)
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                fig_line.update_traces(line_color='#00CC96')
                st.plotly_chart(fig_line, width='stretch')
        else:
            st.info("Start monitoring to generate analytics data.")

    with c2:
        st.subheader("🚦 Current Status")
        st.plotly_chart(create_gauge_chart(st.session_state.score), width='stretch')
        
        if menguap >= 3:
            st.markdown('<div class="alert-box danger">🔴 HIGH RISK: PENGEMUDI MENGANTUK!</div>', unsafe_allow_html=True)
            st.write("Rekomendasi: Segera menepi dan tidur 15-20 menit.")
        elif menguap >= 1:
            st.markdown('<div class="alert-box warning">🟡 WARNING: TANDA KELELAHAN</div>', unsafe_allow_html=True)
            st.write("Rekomendasi: Minum air, buka jendela, atau dengarkan musik.")
        else:
            st.markdown('<div class="alert-box safe">🟢 SAFE: EXCELLENT CONDITION</div>', unsafe_allow_html=True)
            st.write("Pertahankan fokus dan kecepatan aman.")

def page_monitoring():
    st.markdown("## 📷 Live Monitoring")
    
    col_ctrl, col_status = st.columns([1, 3])
    
    with col_ctrl:
        st.write("### Control Panel")
        start_btn = st.button("▶️ Start System", width='stretch', type="primary")
        stop_btn = st.button("⏹ Stop System", width='stretch')
        
        if start_btn:
            if not st.session_state.monitoring:
                try:
                    st.session_state.detector = DrowsinessDetector(model_path="snapdriver_model.h5", yawning_threshold=5)
                    st.session_state.cap = cv2.VideoCapture(0)
                    if not st.session_state.cap.isOpened():
                        st.error("Tidak dapat mengakses webcam. Pastikan webcam tidak digunakan aplikasi lain.")
                        st.session_state.monitoring = False
                        return
                    st.session_state.monitoring = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal memulai sistem: {e}")
                    st.session_state.monitoring = False

        if stop_btn:
            if st.session_state.monitoring:
                st.session_state.monitoring = False
                if st.session_state.cap:
                    st.session_state.cap.release()
                    st.session_state.cap = None
                st.session_state.current_frame = None
                st.rerun()

        st.markdown("---")
        st.info("The system uses a real webcam to detect signs of drowsiness.")

    with col_status:
        video_placeholder = st.empty()
        metrics_placeholder = st.empty()
        alert_placeholder = st.empty()

        if st.session_state.monitoring:
            # Tambahkan jeda kecil di sini untuk memberi waktu "istirahat"
            time.sleep(0.5) 

            cap = st.session_state.cap
            detector = st.session_state.detector
            
            ret, frame = cap.read()
            if ret:
                status, confidence = detector.process_frame(frame)
                
                if status in ["Yawning", "Yawning & Talking"]:
                    kondisi = "Menguap"
                    is_drowsy = True
                else:
                    kondisi = "Normal"
                    is_drowsy = False

                if is_drowsy:
                    st.session_state.score = max(0, st.session_state.score - 5)
                else:
                    st.session_state.score = min(100, st.session_state.score + 1)
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                st.session_state.current_frame = rgb_frame
                st.session_state.current_status = kondisi
                
                waktu = datetime.now().strftime("%H:%M:%S")
                new_data = {"Time": waktu, "Condition": kondisi, "Score": st.session_state.score, "Action": "Alarm Bunyi" if is_drowsy else "Monitoring"}
                st.session_state.riwayat.append(new_data)

                if is_drowsy:
                    play_alarm()

                # Tampilkan UI
                video_placeholder.image(st.session_state.current_frame, caption="Live Feed", channels="RGB", width='stretch')
                
                with alert_placeholder:
                    if is_drowsy:
                        st.error("⚠️ PENGEMUDI MENGANTUK TERDETEKSI!", icon="🚨")
                    else:
                        st.success("✅ You are in a safe condition", icon="🛡️")

                with metrics_placeholder.container():
                    m1, m2 = st.columns(2)
                    m1.metric("Status", kondisi, delta_color="off")
                    m2.metric("Current Score", st.session_state.score, delta= -5 if is_drowsy else 1)
                
                # Rerun untuk update frame berikutnya
                # Jeda yang sedikit lebih panjang mungkin membantu mengurangi flicker
                time.sleep(0.2) 
                st.rerun()
        else:
            video_placeholder.image("https://via.placeholder.com/800x400/000000/FFFFFF?text=SYSTEM+OFFLINE", caption="System Offline", width='stretch')
            alert_placeholder.empty()
            metrics_placeholder.empty()

def page_history():
    st.markdown("## 📊 Monitoring History & Analytics")
    
    if len(st.session_state.riwayat) == 0:
        st.warning("Belum ada data terekam. Silakan jalankan Monitoring terlebih dahulu.")
        return

    df = pd.DataFrame(st.session_state.riwayat)
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Distribution")
        count = df["Kondisi"].value_counts().reset_index()
        count.columns = ["Kondisi", "Jumlah"]
        fig = px.pie(count, values="Jumlah", names="Kondisi", hole=0.4, color="Kondisi", color_discrete_map={"Normal":"#00CC96", "Menguap":"#EF553B"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=True)
        st.plotly_chart(fig, width='stretch')

    with c2:
        st.subheader("📝 Recent Logs")
        st.dataframe(df.tail(10).sort_index(ascending=False), column_config={
            "Kondisi": st.column_config.TextColumn("Kondisi", help="Status Pengemudi", validate="^(Normal|Menguap)$"),
            "Score": st.column_config.ProgressColumn("Safety Score", format="%d", min_value=0, max_value=100),
        }, width='stretch', hide_index=True)

    st.markdown("### 📈 Driver Fatigue Trend")
    fig_area = px.area(df, x="Waktu", y="Score", title="Penurunan Kewaspadaan Seiring Waktu")
    fig_area.update_layout(paper_bgcolor="#262730", plot_bgcolor="#262730", font_color="white")
    fig_area.update_traces(line_color='#636EFA', fillcolor='rgba(99, 110, 250, 0.3)')
    st.plotly_chart(fig_area, width='stretch')

# ==============================
# 5. MAIN APPLICATION LOGIC
# ==============================
if not st.session_state.logged_in:
    page_login()
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3097/3097180.png", width=80)
        st.title("SnapDrive")
        st.caption(f"v2.0 • AI Powered System\n👤 {st.session_state.username}")
        st.markdown("---")
        
        menu = st.radio("Navigation", ["Dashboard", "Monitoring", "History"], captions=["Overview & Score", "Real-time Cam", "Data Logs"])
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        st.slider("Sensitivity", 0, 100, 75)
        st.checkbox("Enable Audio Alert", value=True)
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            if st.session_state.monitoring:
                st.session_state.monitoring = False
                if st.session_state.cap:
                    st.session_state.cap.release()
            st.rerun()
        
        st.caption("© 2025 Binus University\nComputer Vision Project")

    if menu == "Dashboard":
        page_home()
    elif menu == "Monitoring":
        page_monitoring()
    elif menu == "History":
        page_history()