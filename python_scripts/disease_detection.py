import os
import time
import cv2
import numpy as np
import threading
import requests
from datetime import datetime
from ultralytics import YOLO
import torch

from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore, storage

# ===================== LOAD ENV VARIABLES =====================

load_dotenv()

# ===================== CONFIG ================================

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

RTSP_URL = os.getenv("RTSP_URL")
FIREBASE_RTDB = os.getenv("FIREBASE_RTDB")
SERVICE_KEY = os.getenv("SERVICE_KEY")

MODEL_PATH = "ai_model/best.pt"
STORAGE_BUCKET = "your-firebase-storage-bucket"

DISPLAY_W, DISPLAY_H = 640, 480
YOLO_SIZE = 640
TARGET_FPS = 20
FRAME_TIME = 1 / TARGET_FPS

# ===================== OUTPUT DIRECTORIES =====================

os.makedirs("outputs", exist_ok=True)

SAVE_DIR = "outputs/detections"
os.makedirs(SAVE_DIR, exist_ok=True)

# ===================== HSV THRESHOLDS =========================

LOWER_DRY = np.array([10, 40, 40])
UPPER_DRY = np.array([30, 255, 220])

# ===================== FIREBASE INIT =========================

print("=" * 60)
print("AI Smart Agriculture Robot Initializing...")
print("=" * 60)

print("[INFO] Initializing Firebase...")

cred = credentials.Certificate(SERVICE_KEY)

firebase_admin.initialize_app(
    cred,
    {
        "storageBucket": STORAGE_BUCKET
    }
)

db = firestore.client()
bucket = storage.bucket()

print("[SUCCESS] Firebase connection established.")

# ===================== YOLO INIT ==============================

torch.set_grad_enabled(False)

device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[INFO] Running on device: {device}")

if torch.cuda.is_available():
    print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")

model = YOLO(MODEL_PATH)
model.fuse()

print(f"[SUCCESS] YOLO Model Loaded")
print(f"[INFO] Available Classes: {model.names}")

# ===================== HELPER FUNCTIONS =======================

def is_mostly_dry(crop_img, threshold=0.50):

    if crop_img is None or crop_img.size == 0:
        return False

    hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, LOWER_DRY, UPPER_DRY)

    dry_pixels = cv2.countNonZero(mask)

    total_pixels = crop_img.shape[0] * crop_img.shape[1]

    ratio = dry_pixels / total_pixels

    return ratio > threshold


def open_camera():

    print("[INFO] Attempting RTSP Connection...")

    for attempt in range(5):

        print(f"[INFO] Connection Attempt {attempt + 1}")

        cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

        time.sleep(2)

        if cap.isOpened():

            print("[SUCCESS] Camera connected using CAP_FFMPEG")

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            return cap

        print("[WARN] CAP_FFMPEG failed, trying default backend...")

        cap = cv2.VideoCapture(RTSP_URL)

        if cap.isOpened():

            print("[SUCCESS] Camera connected using default backend")

            return cap

        time.sleep(3)

    raise RuntimeError("Could not open RTSP camera")


def fb_get(path):

    try:
        return requests.get(
            f"{FIREBASE_RTDB}{path}.json",
            timeout=1
        ).json()

    except:
        return 0


def fb_set(path, value):

    try:
        requests.put(
            f"{FIREBASE_RTDB}{path}.json",
            json=value,
            timeout=1
        )

    except:
        pass


def upload_image(path, name):

    print(f"[INFO] Uploading {name} to Firebase Storage...")

    blob = bucket.blob(f"detections/{name}")

    blob.upload_from_filename(path)

    blob.make_public()

    return blob.public_url

# ===================== GLOBAL VARIABLES =======================

latest_frame = None
last_logged_label = None
last_logged_time = 0

DUPLICATE_COOLDOWN = 60

# ===================== AUTOMATIC MOVEMENT =====================

def automatic_movement():

    while True:

        mode = fb_get("/mode")

        if mode == 0:

            print("[AUTO MODE] Moving Forward")

            fb_set("/action", 1)

            time.sleep(5)

            print("[AUTO MODE] Stopping")

            fb_set("/action", 0)

            time.sleep(5)

        else:

            time.sleep(2)

# ===================== YOLO DETECTION THREAD ==================

def yolo_worker():

    global latest_frame
    global last_logged_label
    global last_logged_time

    while True:

        if latest_frame is None:

            time.sleep(0.01)

            continue

        frame = latest_frame.copy()

        try:

            results = model.predict(
                frame,
                imgsz=YOLO_SIZE,
                conf=0.30,
                device=device,
                verbose=False
            )[0]

        except Exception as e:

            print(f"[ERROR] YOLO inference failed: {e}")

            continue

        if results.boxes:

            for box in results.boxes:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                conf = float(box.conf[0])

                label = results.names[int(box.cls[0])]

                leaf_crop = frame[y1:y2, x1:x2]

                if is_mostly_dry(leaf_crop, 0.50):
                    label = "Dry Leaf"

                print(f"[DEBUG] Detected: {label} ({conf:.2f})")

                if label != "Dry Leaf" and conf < 0.85:

                    print(f"[INFO] {label} ignored - below threshold")

                    continue

                curr_time = time.time()

                if (
                    label == last_logged_label and
                    (curr_time - last_logged_time) < DUPLICATE_COOLDOWN
                ):

                    print(f"[INFO] Duplicate {label} ignored")

                    continue

                last_logged_label = label
                last_logged_time = curr_time

                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

                fname = f"{label}_{ts}.jpg"

                path = os.path.join(SAVE_DIR, fname)

                draw_img = frame.copy()

                cv2.rectangle(
                    draw_img,
                    (x1, y1),
                    (x2, y2),
                    (0, 165, 255),
                    3
                )

                cv2.putText(
                    draw_img,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2
                )

                cv2.imwrite(path, draw_img)

                url = upload_image(path, fname)

                pos = fb_get("/position_cm") or 0

                db.collection("detections").add({

                    "disease": label,
                    "confidence": round(conf, 2),
                    "position_cm": pos,
                    "image_url": url,
                    "timestamp": datetime.utcnow()

                })

                print(f"[LOGGED] {label} recorded at position {pos} cm")

                fb_set("/detection", 1)

                fb_set("/distance", pos)

                break

        time.sleep(0.05)

# ===================== MAIN APPLICATION =======================

cap = open_camera()

threading.Thread(
    target=yolo_worker,
    daemon=True
).start()

threading.Thread(
    target=automatic_movement,
    daemon=True
).start()

print("[INFO] AgroBot System Fully Active")
print("[INFO] Press 'q' to quit")

try:

    while True:

        ret, frame = cap.read()

        if not ret:

            print("[WARN] Stream lost. Reconnecting...")

            cap.release()

            cap = open_camera()

            continue

        frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

        latest_frame = frame.copy()

        res = model.predict(
            frame,
            imgsz=YOLO_SIZE,
            conf=0.25,
            device=device,
            verbose=False
        )[0]

        display_frame = frame.copy()

        if res.boxes:

            for box in res.boxes:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                conf = float(box.conf[0])

                orig_label = res.names[int(box.cls[0])]

                leaf_crop = frame[y1:y2, x1:x2]

                if is_mostly_dry(leaf_crop, 0.50):

                    display_text = "Dry Leaf"

                    color = (20, 100, 160)

                else:

                    display_text = f"{orig_label} {conf:.2f}"

                    color = (0, 255, 0)

                cv2.rectangle(
                    display_frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                cv2.putText(
                    display_frame,
                    display_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

        cv2.imshow(
            "AgroBot Stream (HSV Guard Active)",
            display_frame
        )

        if cv2.waitKey(1) == ord('q'):
            break

        time.sleep(FRAME_TIME)

except KeyboardInterrupt:

    print("\n[INFO] Manual interrupt received.")

finally:

    cap.release()

    cv2.destroyAllWindows()

    print("[INFO] Shutdown complete.")