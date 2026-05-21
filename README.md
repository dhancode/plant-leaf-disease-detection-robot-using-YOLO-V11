# 🌱 AI-Powered Smart Agriculture Robot

**Detecting plant diseases in real time — using computer vision, a cloud backend, and a physical robot.**

Built with **YOLOv8 · ESP32 · Firebase · Python · OpenCV · PyTorch**

---

## What does this project do?

This robot drives through agricultural fields, streams live video, and **automatically detects plant diseases** using a custom-trained YOLOv8 AI model — all in real time.

Detection results are instantly uploaded to Firebase, making them accessible from anywhere. The robot can be driven manually or switched to **automatic AI-guided navigation**, making it practical for real field use.

---

## How it works — System Overview

```
Camera (RTSP Stream)
        │
        ▼
Python Script ──► YOLOv8 Model ──► Disease Detected
        │                                  │
        ▼                                  ▼
Firebase Realtime DB ◄─────── Detection Log Uploaded
        │
        ▼
ESP32 Controller ──► Robot Movement (Manual / Auto)
```

| Component | Role |
|---|---|
| **YOLOv8** | Detects plant diseases from live video frames |
| **Python scripts** | Processes the video stream and handles Firebase communication |
| **Firebase** | Cloud hub — stores robot commands and detection history |
| **ESP32** | Microcontroller that drives the robot motors |
| **RTSP stream** | Live video feed from the robot's camera |

---

## Features

- Real-time plant disease detection on a live video feed
- Dual navigation — switch between manual control and autonomous AI mode
- Cloud logging — every detection is timestamped and uploaded to Firebase
- Remote monitoring via RTSP stream
- Modular codebase — AI, firmware, and cloud components are cleanly separated

---

## Project Structure

```
smart-agriculture-robot/
├── dataset/              # Training images and annotations
├── ai_model/             # YOLOv8 weights and model config
├── python_scripts/       # Inference pipeline and Firebase sync
├── esp32_code/           # Robot firmware (Arduino IDE)
├── notebook/             # Model training and evaluation notebooks
└── screenshots/          # Sample detection outputs
```

---

## Getting Started

### Requirements

- Python 3.8+
- Firebase project with Realtime Database enabled
- Arduino IDE with ESP32 board support
- A camera supporting RTSP output

### Setup

```bash
# Clone the repo
git clone https://github.com/your-username/smart-agriculture-robot.git
cd smart-agriculture-robot

# Install dependencies
pip install ultralytics opencv-python torch firebase-admin

# Add your Firebase credentials
# Place serviceAccountKey.json in the project root
```

### Run the detection script

```bash
python python_scripts/detect_stream.py --stream <RTSP_URL> --model ai_model/best.pt
```

### Flash the ESP32

Open `esp32_code/robot_controller.ino` in Arduino IDE, enter your Wi-Fi credentials and Firebase config, then upload to the board.

---

## Tech Stack

| Category | Tools |
|---|---|
| AI / Deep Learning | YOLOv8 (Ultralytics), PyTorch |
| Computer Vision | OpenCV |
| Cloud | Firebase Realtime Database |
| Embedded | ESP32, Arduino IDE |
| Language | Python |
| Streaming | RTSP |

---

## Future Plans

- [ ] Mobile app for live dashboards and push alerts
- [ ] GPS-based autonomous field navigation
- [ ] Optimize model for edge deployment (ONNX / TensorRT)
- [ ] Expand disease dataset for higher accuracy
- [ ] Cloud-hosted inference pipeline

---

## Contributors

- Dhanush Santhosh Kumar
- V Indrajith
- Jefin B Joseph
- Midhun PK
