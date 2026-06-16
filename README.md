# 🎯 Advanced AI-Powered Biometric Attendance System

An intelligent facial recognition attendance management system featuring a **Tkinter desktop application** and a **Flask web dashboard**. This system automates attendance tracking using cutting-edge computer vision and machine learning technologies.

![GitHub License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.7+-green.svg)
![Status](https://img.shields.io/badge/status-Active-brightgreen.svg)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Workflow Diagram](#workflow-diagram)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)

---

## 🚀 Overview

The **Advanced AI Biometric Attendance System** is a dual-interface attendance management solution that combines:

- **Desktop Application**: A feature-rich Tkinter GUI for complete attendance management
- **Web Dashboard**: A modern, glassmorphic web interface for real-time monitoring and registration

The system uses **facial recognition technology** to automatically identify and log student attendance, eliminating manual roll calls and preventing proxy attendance.

### Key Highlights

✅ Real-time facial recognition and detection  
✅ Multi-angle face capture (frontal, left, right profiles)  
✅ Robust face detection algorithms  
✅ CSV-based attendance logging  
✅ Student management system  
✅ Dual interface (Desktop + Web)  
✅ Premium dark-themed UI  
✅ Thread-safe operations  

---

## ✨ Features

### 1. **Student Registration**
- Capture 3 snapshots of each student from different angles
- Automatic face detection and extraction
- Store student details (name, email, class)
- Train LBPH facial recognition model

### 2. **Attendance Marking**
- Real-time face detection using Haar Cascades
- LBPH (Local Binary Patterns Histograms) face recognition
- Automatic attendance logging to CSV
- One attendance record per student per day
- Live video feed with face recognition overlay

### 3. **Attendance Management**
- View all attendance records
- Search and filter attendance data
- Calculate total attendance per student
- Export attendance data to CSV

### 4. **Dual Interface**
- **Desktop App**: Full-featured Tkinter application
- **Web Dashboard**: Modern HTML/CSS/JS interface accessible via browser

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Biometric Attendance System                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐          ┌──────────────────┐    │
│  │  Desktop App     │          │  Web Interface   │    │
│  │  (Tkinter)       │          │  (HTML/CSS/JS)   │    │
│  └────────┬─────────┘          └────────┬─────────┘    │
│           │                              │               │
│  ┌────────▼──────────────────────────────▼──────┐      │
│  │   Flask Web Server (web_app.py)              │      │
│  │   - Video streaming endpoint                 │      │
│  │   - Registration API                         │      │
│  │   - Attendance API                           │      │
│  │   - Statistics API                           │      │
│  └────────┬──────────────────────────────────────┘     │
│           │                                              │
│  ┌────────▼──────────────────────────────────────────┐ │
│  │   Computer Vision Engine                          │ │
│  │   - OpenCV (Haar Cascades + LBPH)                │ │
│  │   - Real-time face detection                     │ │
│  │   - Face recognition & matching                 │ │
│  └────────┬──────────────────────────────────────────┘ │
│           │                                              │
│  ┌────────▼──────────────────────────────────────────┐ │
│  │   Data Storage                                    │ │
│  │   - training_images/ (Face snapshots)             │ │
│  │   - students.csv (Student data)                  │ │
│  │   - attendance.csv (Attendance logs)             │ │
│  └──────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Workflow Diagram

### Student Registration Flow
```
START
  │
  ├─► User fills student details (Name, Email, Class)
  │   │
  │   ├─► Webcam activated
  │   │
  │   ├─► Capture Snapshot 1 (Look Straight)
  │   │   └─► Extract & store face region
  │   │
  │   ├─► Capture Snapshot 2 (Turn Left)
  │   │   └─► Extract & store face region
  │   │
  │   ├─► Capture Snapshot 3 (Turn Right)
  │   │   └─► Extract & store face region
  │   │
  │   ├─► Save 3 images to training_images/
  │   │
  │   ├─► Save student info to students.csv
  │   │
  │   ├─► Train LBPH model with new images
  │   │
  │   └─► Display success notification
  │
END
```

### Attendance Marking Flow
```
START
  │
  ├─► System loads trained LBPH model
  │
  ├─► Open webcam video stream
  │
  ├─► For each video frame:
  │   │
  │   ├─► Detect faces using Haar Cascade
  │   │
  │   ├─► For each detected face:
  │   │   │
  │   │   ├─► Recognize using LBPH model
  │   │   │
  │   │   ├─► If confidence < 65 (Match found):
  │   │   │   ├─► Extract student name
  │   │   │   ├─► Check if already marked today
  │   │   │   ├─► Log to attendance.csv
  │   │   │   └─► Display green "PRESENT" label
  │   │   │
  │   │   └─► Else (Unknown):
  │   │       └─► Display red "UNKNOWN" label
  │   │
  │   └─► Continue streaming
  │
  ├─► User presses ESC to stop
  │
  └─► Close camera & release resources
END
```

---

## 🛠️ Technologies Used

### **Backend Technologies**

| Technology | Purpose | Version |
|-----------|---------|---------|
| **Python** | Core programming language | 3.7+ |
| **Flask** | Web framework for API endpoints | Latest |
| **OpenCV** | Computer vision & face detection/recognition | opencv-contrib-python |
| **NumPy** | Numerical computations & array operations | Latest |
| **Pandas** | CSV data handling & manipulation | Latest |
| **Tkinter** | Desktop GUI framework | Built-in |

### **Computer Vision Algorithms**

| Algorithm | Application | Description |
|-----------|------------|-------------|
| **Haar Cascades** | Face Detection | Cascade classifiers for detecting faces (frontal & profile) |
| **LBPH** | Face Recognition | Local Binary Patterns Histograms for facial feature matching |
| **Face Cropping** | Feature Extraction | Extract face regions for model training |

### **Frontend Technologies**

| Technology | Purpose |
|-----------|---------|
| **HTML5** | Markup & structure |
| **CSS3** | Styling & animations (Glassmorphism effect) |
| **Vanilla JavaScript** | Client-side interactivity |
| **MJPEG Stream** | Real-time video streaming to browser |

### **Data Storage**

| Format | Purpose |
|--------|---------|
| **CSV** | Student details and attendance logs |
| **JPG Images** | Training data for facial recognition |

---

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- Webcam/USB camera
- Windows, macOS, or Linux OS

### Step 1: Clone Repository
```bash
git clone https://github.com/sharukh101/Biometric-Attendance-system.git
cd Biometric-Attendance-system
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Required Directories
```bash
mkdir training_images
```

---

## 🎮 Usage

### Option 1: Run Desktop Application
```bash
python attendance_sys.py
```

**Features:**
- Register new students
- Mark attendance
- View attendance records
- Search and statistics

### Option 2: Run Web Dashboard
```bash
python web_app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

**Features:**
- Register students via web interface
- Real-time attendance marking with live video feed
- View attendance statistics
- Responsive glassmorphic design

---

## 📁 Project Structure

```
Biometric-Attendance-system/
│
├── attendance_sys.py           # Desktop Tkinter application
├── web_app.py                  # Flask web server
├── index.html                  # Web dashboard UI
├── requirements.txt            # Python dependencies
│
├── training_images/            # Directory for face snapshots (auto-created)
│   ├── STUDENT_NAME 1.jpg
│   ├── STUDENT_NAME 2.jpg
│   └── STUDENT_NAME 3.jpg
│
├── students.csv                # Student database
│   ├── Name | Email | Class
│   └── Data rows...
│
├── attendance.csv              # Attendance logs
│   ├── Name | Time | Date
│   └── Records...
│
└── README.md                   # This file
```

---

## 🧠 How It Works

### Face Detection Process
The system uses **Haar Cascade Classifiers** for robust face detection:

1. **Frontal Face Detection** - Primary cascade for faces looking directly at camera
2. **Profile Face Detection** - Secondary cascade for side-angled faces
3. **Horizontal Flip Detection** - Handles faces at opposite angle profiles
4. **Multi-scale Detection** - Tries different scale factors for varied face sizes

**Code Example:**
```python
def detect_faces_robust(gray):
    # Try frontal cascade
    frontal_cascade = cv2.CascadeClassifier(...)
    faces = frontal_cascade.detectMultiScale(gray, 1.15, 4)
    if len(faces) > 0:
        return faces
    
    # Try profile cascade
    profile_cascade = cv2.CascadeClassifier(...)
    faces = profile_cascade.detectMultiScale(gray, 1.15, 3)
    if len(faces) > 0:
        return faces
    
    return []
```

### Face Recognition Process
The system uses **LBPH (Local Binary Patterns Histograms)** for recognition:

1. **Model Training** - Train LBPH model with known face images
2. **Face Preprocessing** - Resize and normalize detected faces
3. **Feature Extraction** - Extract LBP histograms from face regions
4. **Matching** - Compare test face features against trained model
5. **Confidence Scoring** - Score < 65 indicates a match

**Code Example:**
```python
# Train model
model = cv2.face.LBPHFaceRecognizer_create()
model.train(training_data, labels)

# Recognize in video stream
id, confidence = model.predict(face_roi)
if confidence < 65:
    name = recognized_students[id]
    save_attendance(name)
```

### Data Flow
```
Webcam Input
    ↓
Convert to Grayscale
    ↓
Detect Faces (Haar Cascade)
    ↓
Recognize Face (LBPH Model)
    ↓
Match Found?
    ├─► Yes: Save to attendance.csv, Show "PRESENT"
    └─► No: Show "UNKNOWN"
```

---

## 🔮 Future Enhancements

- [ ] **Deep Learning Models** - Integrate deep neural networks (FaceNet, VGGFace2)
- [ ] **Database Integration** - Replace CSV with SQL database (PostgreSQL/MySQL)
- [ ] **Cloud Deployment** - Deploy web app to cloud platforms (AWS, Google Cloud)
- [ ] **Mobile App** - Develop mobile application for iOS/Android
- [ ] **Multi-face Detection** - Process multiple faces simultaneously
- [ ] **Email Notifications** - Send attendance reports via email
- [ ] **Voice Alerts** - Audio feedback during attendance marking
- [ ] **Liveness Detection** - Prevent spoofing with photo/video attacks
- [ ] **Advanced Analytics** - Generate detailed attendance reports and insights
- [ ] **API Authentication** - Implement JWT/OAuth2 for security
- [ ] **Real-time Dashboard** - WebSocket integration for live updates
- [ ] **Attendance Patterns** - Machine learning to predict attendance trends

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Sharukh Ahmed**

- GitHub: [@sharukh101](https://github.com/sharukh101)
- Project: [Biometric-Attendance-system](https://github.com/sharukh101/Biometric-Attendance-system)

---

## 📞 Support & Contact

For issues, questions, or suggestions, please:
- Open an issue on GitHub
- Contact via email or social media

---

## 🙏 Acknowledgments

- OpenCV team for excellent computer vision library
- Python community for amazing tools and frameworks
- Flask team for lightweight web framework
- All contributors and users

---

## 📚 Resources & References

- [OpenCV Documentation](https://docs.opencv.org/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [LBPH Face Recognition](https://en.wikipedia.org/wiki/Local_binary_patterns)
- [Haar Cascades](https://en.wikipedia.org/wiki/Haar-like_features)

---

**Made with ❤️ by Sharukh Ahmed**

⭐ If you find this project useful, please consider giving it a star!
