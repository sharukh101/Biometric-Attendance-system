import os
import cv2
import numpy as np
import pandas as pd
import time
import threading
from datetime import datetime
from flask import Flask, render_template, Response, jsonify, request

app = Flask(__name__, template_folder='.')

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.before_request
def handle_options_requests():
    if request.method == 'OPTIONS':
        response = app.make_response(('', 204))
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return response


# Setup Directories
if not os.path.exists('training_images'):
    os.makedirs('training_images')

def robust_video_capture():
    """Tries to find and open an active webcam device by searching indices 0, 1, 2."""
    for index in [0, 1, 2]:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"[CAMERA SUCCESS] Opened webcam at index {index} using default backend.")
                return cap
            cap.release()

    for index in [0, 1, 2]:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"[CAMERA SUCCESS] Opened webcam at index {index} using CAP_DSHOW backend.")
                return cap
            cap.release()

    print("[CAMERA ERROR] No active webcam found at indices 0, 1, or 2.")
    return None


def detect_faces_robust(gray):
    """Detects faces using both frontal and profile cascades to handle turned/angled faces."""
    frontal_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 1. Try frontal face cascade with fine search scale factor and lenient neighbor count
    faces = frontal_cascade.detectMultiScale(gray, 1.15, 4)
    if len(faces) > 0:
        return faces
        
    # 2. Try frontal face cascade with even finer scale factor and lower neighbors count
    faces = frontal_cascade.detectMultiScale(gray, 1.1, 3)
    if len(faces) > 0:
        return faces

    # 3. Try profile face cascade
    profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
    faces = profile_cascade.detectMultiScale(gray, 1.15, 3)
    if len(faces) > 0:
        return faces

    # 4. Try profile face cascade on horizontally flipped image (for opposite direction profile)
    flipped = cv2.flip(gray, 1)
    faces_flipped = profile_cascade.detectMultiScale(flipped, 1.15, 3)
    if len(faces_flipped) > 0:
        w_img = gray.shape[1]
        mapped_faces = []
        for (xf, yf, wf, hf) in faces_flipped:
            x_orig = w_img - xf - wf
            mapped_faces.append([x_orig, yf, wf, hf])
        return mapped_faces

    return []

def save_student_details(name, email, class_name):
    """Saves student name, email, and class/semester to students.csv."""
    header = ["Name", "Email", "Class"]
    csv_file = 'students.csv'
    
    with csv_lock:
        if not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0:
            pd.DataFrame(columns=header).to_csv(csv_file, index=False)
        
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            df = pd.DataFrame(columns=header)
            
        df['Name'] = df['Name'].astype(str).str.upper().str.strip()
        
        # If exists, update
        if name in df['Name'].values:
            df.loc[df['Name'] == name, ['Email', 'Class']] = [email, class_name]
        else:
            new_row = pd.DataFrame([[name, email, class_name]], columns=header)
            df = pd.concat([df, new_row], ignore_index=True)
            
        df.to_csv(csv_file, index=False)

# Global variables for controlling camera state
camera_active = False
camera_lock = threading.Lock()
csv_lock = threading.Lock()

def extract_student_name(filename):
    """Robust helper to extract a clean student name from their training image filename."""
    base = os.path.splitext(filename)[0]
    # base is e.g. "SSS 1" or "Sharukh-2_1" or "sazid-1"
    if '_' in base:
        parts = base.split('_')
        if parts[-1].isdigit():
            return "_".join(parts[:-1]).upper()
        return base.upper()
    elif ' ' in base:
        parts = base.split(' ')
        if parts[-1].isdigit():
            return " ".join(parts[:-1]).upper()
        return base.upper()
    elif '-' in base:
        parts = base.split('-')
        if parts[-1].isdigit():
            return "-".join(parts[:-1]).upper()
        return base.upper()
    return base.upper()

def get_registered_students():
    """Helper to extract unique registered student names from files in training_images."""
    if not os.path.exists('training_images'):
        return []
    files = [f for f in os.listdir('training_images') if f.endswith(('.jpg', '.png', '.jpeg'))]
    students = set()
    for f in files:
        name = extract_student_name(f)
        if name:
            students.add(name)
    return sorted(list(students))

def get_trained_model():
    """Reads training images, extracts name mapping, trains the LBPH model, and returns it."""
    files = [f for f in os.listdir('training_images') if f.endswith(('.jpg', '.png', '.jpeg'))]
    if not files:
        return None, []

    training_data, labels, names = [], [], []
    
    # Sort files to ensure stable indices
    files.sort()
    
    for i, f in enumerate(files):
        img_path = os.path.join('training_images', f)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            training_data.append(cv2.resize(img, (200, 200)))
            labels.append(i)
            names.append(extract_student_name(f))

    if not training_data:
        return None, []

    model = cv2.face.LBPHFaceRecognizer_create()
    model.train(np.asarray(training_data), np.asarray(labels))
    return model, names

def save_to_csv(name):
    """Saves the student attendance record to attendance.csv if not already present for today."""
    header = ["Name", "Time", "Date"]
    today = datetime.now().strftime("%d-%m-%Y")
    
    with csv_lock:
        try:
            df = pd.read_csv('attendance.csv')
        except (pd.errors.EmptyDataError, FileNotFoundError):
            df = pd.DataFrame(columns=header)
            df.to_csv('attendance.csv', index=False)
        
        df['Name'] = df['Name'].astype(str)
        df['Date'] = df['Date'].astype(str)
        
        if not ((df['Name'] == name) & (df['Date'] == today)).any():
            new_row = pd.DataFrame([[name, datetime.now().strftime('%H:%M:%S'), today]], columns=header)
            new_row.to_csv('attendance.csv', mode='a', header=False, index=False)

def create_error_frame(message):
    """Creates a black placeholder JPEG frame with an error message inside it."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Dark modern background (#151621)
    img[:] = (33, 22, 21) 
    cv2.putText(img, message, (80, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (80, 76, 231), 2)
    ret, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

def generate_frames():
    """Generates JPEG frame stream with real-time face detection and LBPH recognition."""
    global camera_active
    cap = None
    
    try:
        # Load and train face model
        model, names = get_trained_model()
        if model is None:
            frame = create_error_frame("Please register at least one student first!")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            return

        # Load cascade
        face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initialize camera
        cap = robust_video_capture()
        if cap is None:
            frame = create_error_frame("Webcam is in use or not connected!")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            return

        camera_active = True

        while camera_active:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                id, conf = model.predict(roi)
                
                # A confidence score below 65 indicates a solid match in LBPH
                if conf < 65:
                    name = names[id].upper()
                    save_to_csv(name)
                    
                    # Modern Emerald Green overlay (#2ecc71)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (113, 204, 46), 2)
                    # Text box background
                    cv2.rectangle(frame, (x, y-35), (x+w, y), (113, 204, 46), cv2.FILLED)
                    cv2.putText(frame, f"{name} (Present)", (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                else:
                    # Modern Red overlay for unknown (#e74c3c)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (60, 76, 231), 2)
                    # Text box background
                    cv2.rectangle(frame, (x, y-35), (x+w, y), (60, 76, 231), cv2.FILLED)
                    cv2.putText(frame, "UNKNOWN STUDENT", (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Minimal sleep to prevent maxing out the CPU cores
            time.sleep(0.03)

    except GeneratorExit:
        # Fired when the browser client stops listening/navigates away
        pass
    except Exception as e:
        print(f"Error streaming camera: {e}")
    finally:
        camera_active = False
        if cap is not None:
            cap.release()

# ----------------- FLASK WEB API ROUTES -----------------

@app.route('/')
def home():
    """Renders the single-page application dashboard."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route for marking attendance."""
    global camera_active
    camera_active = True
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stop_attendance', methods=['POST'])
def stop_attendance():
    """Stops the camera stream."""
    global camera_active
    camera_active = False
    return jsonify({"success": True, "message": "Webcam stream stopped successfully."})

@app.route('/api/stats')
def get_stats():
    """Returns attendance statistics for the dashboard UI."""
    total_students = len(get_registered_students())
    
    today = datetime.now().strftime("%d-%m-%Y")
    today_count = 0
    
    try:
        with csv_lock:
            df = pd.read_csv('attendance.csv')
            df['Date'] = df['Date'].astype(str)
            today_count = len(df[df['Date'] == today]['Name'].unique())
    except (pd.errors.EmptyDataError, FileNotFoundError):
        pass
    except Exception as e:
        print(f"Error calculating stats: {e}")

    return jsonify({
        "total_students": total_students,
        "marked_today": today_count,
        "camera_active": camera_active,
        "date": today
    })

@app.route('/api/students')
def list_students():
    """Returns a list of all registered student names."""
    return jsonify(get_registered_students())

@app.route('/api/register_student', methods=['POST'])
def register_student():
    """Registers a student by opening the camera locally and capturing 3 snapshots."""
    global camera_active
    
    # Block registration if camera is currently streaming face detection
    if camera_active:
        return jsonify({
            "success": False, 
            "message": "Webcam is currently in use for marking attendance! Please stop the scanner first."
        }), 400
        
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"success": False, "message": "Student Name is required!"}), 400
        
    name = data['name'].strip().upper()
    if not name:
        return jsonify({"success": False, "message": "Student Name cannot be blank!"}), 400

    # Open camera to capture 3 snapshots
    cap = robust_video_capture()
    if cap is None:
        return jsonify({"success": False, "message": "Cannot open webcam. It might be locked by another application."}), 500

    face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    count = 0
    max_frames_to_try = 150 # prevention from infinite loop if face is not visible
    frames_tried = 0

    try:
        while count < 3 and frames_tried < max_frames_to_try:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames_tried += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_classifier.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                count += 1
                img_path = os.path.join('training_images', f"{name}_{count}.jpg")
                cv2.imwrite(img_path, gray[y:y+h, x:x+w])
                break # Only capture one face image per frame
            
            time.sleep(0.12) # Short interval between captures

    except Exception as e:
        return jsonify({"success": False, "message": f"Error during face capture: {str(e)}"}), 500
    finally:
        cap.release()

    if count < 3:
        return jsonify({
            "success": False, 
            "message": f"Could not capture enough clear face photos. Captured {count}/3. Please ensure your face is clearly visible in the camera!"
        }), 400

    # Attempt to load model to verify it trains successfully
    try:
        get_trained_model()
    except Exception as e:
        return jsonify({
            "success": True, 
            "message": f"Captured photos, but LBPH model failed to train: {str(e)}"
        })

    return jsonify({
        "success": True, 
        "message": f"Successfully registered '{name}'! 3 face snapshots have been trained."
    })

@app.route('/api/attendance_records')
def get_attendance_records():
    """Reads attendance.csv and returns all entries, sorted newest first."""
    try:
        with csv_lock:
            df = pd.read_csv('attendance.csv')
            df = df.fillna('')
            records = df.to_dict(orient='records')
        records.reverse()  # Newest first
        return jsonify(records)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Global variable for registration camera state
register_camera_active = False
current_register_frame = None
active_cap = None

def generate_register_frames():
    """Generates JPEG frames for the registration viewfinder camera."""
    global register_camera_active, active_cap, current_register_frame
    try:
        active_cap = robust_video_capture()
        if active_cap is None:
            frame = create_error_frame("Webcam is locked or not connected!")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            return

        register_camera_active = True

        while register_camera_active:
            ret, frame = active_cap.read()
            if not ret:
                break

            # Store frame copy globally for manual capture snapshotting
            current_register_frame = frame.copy()

            # Process frame for visual feedback overlay (face bounding box)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detect_faces_robust(gray)
            for (x, y, w, h) in faces:
                # Draw neon yellow alignment frame box
                cv2.rectangle(frame, (x, y), (x+w, y+h), (50, 200, 240), 2)
                break  # Draw box for first detected face only

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.04)

    except GeneratorExit:
        pass
    except Exception as e:
        print(f"Error in register camera stream: {e}")
    finally:
        register_camera_active = False
        current_register_frame = None
        if active_cap is not None:
            active_cap.release()
            active_cap = None

@app.route('/register_feed')
def register_feed():
    """Video streaming route for manual registration snapshots."""
    global register_camera_active
    register_camera_active = True
    return Response(generate_register_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Global dictionary to store captured face images in memory before registration finalization
temp_captured_faces = {}

@app.route('/api/capture_snap', methods=['POST'])
def capture_snap():
    """Processes the current register webcam frame to crop and hold in memory."""
    global current_register_frame, register_camera_active, active_cap, temp_captured_faces
    
    frame = current_register_frame
    if not register_camera_active or frame is None:
        return jsonify({"success": False, "message": "Registration camera is offline! Open it first."}), 400

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"success": False, "message": "Student Name is required!"}), 400

    name = data['name'].strip().upper()
    if not name:
        return jsonify({"success": False, "message": "Student Name cannot be blank!"}), 400

    # Retrieve step from request body for manual capture synchronization
    step = data.get('step')
    if step is not None:
        try:
            step = int(step)
        except ValueError:
            step = None

    if step is None:
        # Fallback to index-counting logic if step is not supplied
        step = len(temp_captured_faces.get(name, [])) + 1
        if step > 3:
            temp_captured_faces[name] = []
            step = 1

    # Initialize list for this student on step 1 and clean up old permanent snapshots
    if step == 1:
        temp_captured_faces[name] = []
        existing_snaps = [f for f in os.listdir('training_images') if (f.startswith(f"{name}_") or f.startswith(f"{name} ")) and f.endswith('.jpg')]
        for f in existing_snaps:
            try:
                os.remove(os.path.join('training_images', f))
            except:
                pass

    # Detect face in the current frame snapshot
    frame_copy = frame.copy()
    gray = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
    faces = detect_faces_robust(gray)

    if len(faces) == 0:
        return jsonify({"success": False, "message": "No face detected! Please ensure your face is fully visible in the camera viewfinder."}), 400

    # Crop and store face image array in memory (not disk)
    (x, y, w, h) = faces[0]
    cropped_face = gray[y:y+h, x:x+w].copy()
    
    if len(temp_captured_faces[name]) < step:
        temp_captured_faces[name].append(cropped_face)
    else:
        temp_captured_faces[name][step - 1] = cropped_face

    is_complete = (step == 3)

    return jsonify({
        "success": True,
        "count": step,
        "is_complete": is_complete,
        "message": f"Face Snapshot {step}/3 captured successfully in memory!"
    })

@app.route('/api/finalize_registration', methods=['POST'])
def finalize_registration():
    """Writes memory-held snapshots to disk and trains the facial recognition model."""
    global temp_captured_faces
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data or 'class_name' not in data:
        return jsonify({"success": False, "message": "Student Name, Email, and Class/Semester are all required!"}), 400

    name = data['name'].strip().upper()
    email = data['email'].strip()
    class_name = data['class_name'].strip().upper()

    if not name or not email or not class_name:
        return jsonify({"success": False, "message": "All fields (Name, Email, and Class/Semester) are compulsory!"}), 400

    # Verify that the 3 snapshots exist in memory
    if name not in temp_captured_faces or len(temp_captured_faces[name]) < 3:
        return jsonify({
            "success": False, 
            "message": "Captured snapshots are missing or incomplete! Please capture all 3 snapshots before registering."
        }), 400

    # Save memory images permanently to disk
    try:
        # Clean up any potential files in training_images
        existing_snaps = [f for f in os.listdir('training_images') if (f.startswith(f"{name}_") or f.startswith(f"{name} ")) and f.endswith('.jpg')]
        for f in existing_snaps:
            try:
                os.remove(os.path.join('training_images', f))
            except:
                pass
                
        # Write to disk
        for i, face_img in enumerate(temp_captured_faces[name]):
            img_path = os.path.join('training_images', f"{name} {i+1}.jpg")
            cv2.imwrite(img_path, face_img)
            
        # Save details to students.csv
        save_student_details(name, email, class_name)
            
        # Clear memory
        del temp_captured_faces[name]
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save snapshots: {str(e)}"}), 500

    # Train recognition model using the csv_lock
    try:
        get_trained_model()
    except Exception as e:
        print(f"Error training recognition model during finalization: {e}")
        return jsonify({
            "success": False, 
            "message": f"Model training failed: {str(e)}"
        }), 500

    return jsonify({
        "success": True, 
        "message": f"Successfully registered '{name}'! Model trained successfully."
    })

@app.route('/api/stop_register_camera', methods=['POST'])
def stop_register_camera():
    """Stops the registration webcam preview stream and releases resources."""
    global register_camera_active, active_cap
    register_camera_active = False
    if active_cap is not None:
        active_cap.release()
        active_cap = None
    return jsonify({"success": True, "message": "Registration viewfinder deactivated."})

if __name__ == '__main__':
    print("--------------------------------------------------")
    print("Starting AI Attendance Web App on http://localhost:5000")
    print("--------------------------------------------------")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
