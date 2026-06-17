import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import pandas as pd

# Setup Directories
if not os.path.exists('training_images'): os.makedirs('training_images')

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


def extract_student_name(filename):
    """Robust helper to extract clean student name from their training image filename."""
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

def show_desktop_toast(parent, title, message):
    """Shows a non-blocking modern dark-themed toast notification in the bottom-right corner of the screen."""
    toast_win = tk.Toplevel(parent)
    toast_win.overrideredirect(True) # Remove title bar and borders
    toast_win.configure(bg="#181922") # Premium dark background
    toast_win.attributes("-topmost", True) # Keep it on top of other windows
    
    # Border wrapper to simulate a glowing border
    border_frame = tk.Frame(toast_win, bg="#27ae60", bd=1)
    border_frame.pack(fill=tk.BOTH, expand=True)
    
    content_frame = tk.Frame(border_frame, bg="#181922", padx=15, pady=12)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_lbl = tk.Label(content_frame, text=title, font=("Arial", 11, "bold"), fg="#27ae60", bg="#181922")
    title_lbl.pack(anchor="w")
    
    # Message
    msg_lbl = tk.Label(content_frame, text=message, font=("Arial", 9), fg="#e2e8f0", bg="#181922")
    msg_lbl.pack(anchor="w", pady=(4, 0))
    
    # Position in the bottom-right corner
    screen_width = toast_win.winfo_screenwidth()
    screen_height = toast_win.winfo_screenheight()
    
    width = 300
    height = 75
    
    # Position: 30px from right, 80px from bottom (above taskbar)
    x = screen_width - width - 30
    y = screen_height - height - 80
    
    toast_win.geometry(f"{width}x{height}+{x}+{y}")
    
    # Simple fade-in animation by animating opacity (on Windows)
    try:
        toast_win.attributes("-alpha", 0.0)
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.1
                toast_win.attributes("-alpha", alpha)
                toast_win.after(20, lambda: fade_in(alpha))
        fade_in()
    except Exception:
        # Fallback if alpha is not supported
        toast_win.attributes("-alpha", 1.0)
        
    # Auto-destroy after 5 seconds
    def fade_out_and_destroy(alpha=1.0):
        if alpha > 0.0:
            alpha -= 0.1
            toast_win.attributes("-alpha", alpha)
            toast_win.after(20, lambda: fade_out_and_destroy(alpha))
        else:
            toast_win.destroy()
            
    toast_win.after(5000, lambda: fade_out_and_destroy())

class AttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced AI Attendance System")
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")

        # Load Models
        self.face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.model = cv2.face.LBPHFaceRecognizer_create()
        self.create_ui()

    def create_ui(self):
        # Header
        header = tk.Label(self.root, text="Student Management & Attendance", font=("Arial", 24, "bold"), bg="#34495e", fg="white", pady=20)
        header.pack(fill=tk.X)

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#2c3e50")
        btn_frame.pack(pady=30)

        # 1. Registration
        tk.Button(btn_frame, text="1. Register New Student", font=("Arial", 12), width=25, command=self.register_student, bg="#27ae60", fg="white").grid(row=0, column=0, padx=10, pady=10)
        # 2. Mark Attendance
        tk.Button(btn_frame, text="2. Start Marking Attendance", font=("Arial", 12), width=25, command=self.start_attendance, bg="#2980b9", fg="white").grid(row=0, column=1, padx=10, pady=10)
        # 3. View All
        tk.Button(btn_frame, text="3. View All Attendance", font=("Arial", 12), width=25, command=self.view_attendance, bg="#f39c12", fg="white").grid(row=1, column=0, padx=10, pady=10)
        # 4. Search Stats
        tk.Button(btn_frame, text="4. Search & Total Stats", font=("Arial", 12), width=25, command=self.search_stats, bg="#8e44ad", fg="white").grid(row=1, column=1, padx=10, pady=10)

    def register_student(self):
        reg_win = tk.Toplevel(self.root)
        reg_win.title("Registration")
        reg_win.geometry("350x420")
        reg_win.configure(bg="#2c3e50")
        
        tk.Label(reg_win, text="Student Full Name *:", font=("Arial", 11), bg="#2c3e50", fg="white").pack(pady=5)
        name_var = tk.StringVar()
        name_entry = tk.Entry(reg_win, textvariable=name_var, font=("Arial", 11))
        name_entry.pack(pady=5)

        tk.Label(reg_win, text="Email Address *:", font=("Arial", 11), bg="#2c3e50", fg="white").pack(pady=5)
        email_var = tk.StringVar()
        email_entry = tk.Entry(reg_win, textvariable=email_var, font=("Arial", 11))
        email_entry.pack(pady=5)

        tk.Label(reg_win, text="Class/Semester *:", font=("Arial", 11), bg="#2c3e50", fg="white").pack(pady=5)
        class_var = tk.StringVar()
        class_entry = tk.Entry(reg_win, textvariable=class_var, font=("Arial", 11))
        class_entry.pack(pady=5)

        self.capture_completed = False
        self.camera_running = False
        self.captured_count = 0
        self.latest_raw_frame = None
        self.temp_faces = []
        self.instruction_text = ""

        def start_camera():
            name = name_var.get().upper().strip()
            email = email_var.get().strip()
            class_name = class_var.get().upper().strip()
            if not name or not email or not class_name: 
                messagebox.showerror("Error", "All fields (Name, Email, Class) are compulsory!")
                return
            
            if self.camera_running:
                return
            self.cap = robust_video_capture()
            if self.cap is None:
                messagebox.showerror("Error", "Cannot open webcam!")
                return
                
            self.camera_running = True
            self.captured_count = 0
            self.latest_raw_frame = None
            self.temp_faces = []
            self.instruction_text = "LOOK STRAIGHT"
            
            # Disable inputs during camera capture
            name_entry.config(state=tk.DISABLED)
            email_entry.config(state=tk.DISABLED)
            class_entry.config(state=tk.DISABLED)
            
            btn_start.config(state=tk.DISABLED)
            btn_cap.config(state=tk.NORMAL, text="Capture Snapshot (1/3) - Look Straight")
            btn_reg.config(state=tk.DISABLED)
            
            # Clean up old files for this student (both space and underscore formats)
            for i in range(1, 4):
                for fmt in [f"training_images/{name}_{i}.jpg", f"training_images/{name} {i}.jpg"]:
                    try:
                        os.remove(fmt)
                    except:
                        pass
            
            update_preview()

        def update_preview():
            if not self.camera_running:
                return
                
            ret, frame = self.cap.read()
            if not ret:
                stop_camera()
                return
                
            self.latest_raw_frame = frame.copy()
            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detect_faces_robust(gray)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                break
                
            cv2.putText(display_frame, f"Snapshots: {self.captured_count}/3", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            if self.instruction_text:
                cv2.putText(display_frame, self.instruction_text, (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                cv2.putText(display_frame, "Click 'Capture Snapshot' in app", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Resize preview to make camera display height smaller while keeping width same
            small_frame = cv2.resize(display_frame, (640, 360))
            cv2.imshow("Registration Preview", small_frame)
            cv2.waitKey(1)
            
            reg_win.after(30, update_preview)

        def stop_camera():
            self.camera_running = False
            self.instruction_text = ""
            if self.cap:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()
            
            # Enable inputs again
            name_entry.config(state=tk.NORMAL)
            email_entry.config(state=tk.NORMAL)
            class_entry.config(state=tk.NORMAL)
            
            btn_start.config(state=tk.NORMAL)
            btn_cap.config(state=tk.DISABLED, text="Capture Snapshot")

        def capture_single_step():
            if not self.camera_running:
                return
            
            name = name_var.get().upper().strip()
            email = email_var.get().strip()
            class_name = class_var.get().upper().strip()
            if not name or not email or not class_name:
                messagebox.showerror("Error", "All fields (Name, Email, Class) are compulsory!")
                return
                
            step = self.captured_count + 1
            if step > 3:
                return
                
            if self.latest_raw_frame is None:
                messagebox.showerror("Error", "No camera frame available yet. Please wait.")
                return
                
            gray = cv2.cvtColor(self.latest_raw_frame, cv2.COLOR_BGR2GRAY)
            faces = detect_faces_robust(gray)
            
            if len(faces) == 0:
                messagebox.showerror("Error", "No face detected! Please ensure your face is fully visible in the camera viewfinder.")
                return
                
            (x, y, w, h) = faces[0]
            self.temp_faces.append(gray[y:y+h, x:x+w].copy())
            self.captured_count = step
            
            # Show visual green flash feedback
            flash_frame = self.latest_raw_frame.copy()
            cv2.rectangle(flash_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(flash_frame, f"SNAPSHOT {step}/3 CAPTURED!", (150, 180), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            small_flash = cv2.resize(flash_frame, (640, 360))
            cv2.imshow("Registration Preview", small_flash)
            cv2.waitKey(400) # Wait a bit for the flash feedback
            
            if step == 3:
                self.capture_completed = True
                self.instruction_text = "Snapshots completed. Click Register."
                btn_cap.config(state=tk.DISABLED, text="Snapshots Completed")
                btn_reg.config(state=tk.NORMAL)
            else:
                next_step = step + 1
                next_angle = "Turn Left" if next_step == 2 else "Turn Right"
                self.instruction_text = next_angle.upper()
                btn_cap.config(text=f"Capture Snapshot ({next_step}/3) - {next_angle}")

        def register():
            name = name_var.get().upper().strip()
            email = email_var.get().strip()
            class_name = class_var.get().upper().strip()
            if not name or not email or not class_name:
                messagebox.showerror("Error", "All fields (Name, Email, Class) are compulsory!")
                return
            if not self.capture_completed or len(self.temp_faces) < 3:
                messagebox.showerror("Error", "Please capture images first!")
                return
            
            try:
                # Save snapshots permanently to disk
                for i, face_img in enumerate(self.temp_faces):
                    img_path = f"training_images/{name} {i+1}.jpg"
                    cv2.imwrite(img_path, face_img)
                
                # Save student details to students.csv
                save_student_details(name, email, class_name)
                
                self.temp_faces = []
                show_desktop_toast(self.root, "Registration Successful", f"Registered '{name}' successfully!")
                reg_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save snapshots: {str(e)}")

        def on_close():
            stop_camera()
            reg_win.destroy()

        reg_win.protocol("WM_DELETE_WINDOW", on_close)

        btn_start = tk.Button(reg_win, text="Start Camera Feed", font=("Arial", 10, "bold"), width=20, command=start_camera, bg="#2980b9", fg="white")
        btn_start.pack(pady=10)

        btn_cap = tk.Button(reg_win, text="Capture Snapshot", font=("Arial", 10, "bold"), width=25, command=capture_single_step, bg="#e67e22", fg="white", state=tk.DISABLED)
        btn_cap.pack(pady=10)

        btn_reg = tk.Button(reg_win, text="Register", font=("Arial", 10, "bold"), width=20, command=register, bg="#27ae60", fg="white", state=tk.DISABLED)
        btn_reg.pack(pady=10)

    def start_attendance(self):
        files = [f for f in os.listdir('training_images') if f.endswith(('.jpg', '.png'))]
        if not files:
            messagebox.showerror("Error", "No students registered!")
            return

        training_data, labels, names = [], [], []
        for i, f in enumerate(files):
            img = cv2.imread(f"training_images/{f}", cv2.IMREAD_GRAYSCALE)
            training_data.append(cv2.resize(img, (200,200)))
            labels.append(i)
            names.append(extract_student_name(f))

        self.model.train(np.asarray(training_data), np.asarray(labels))
        cap = robust_video_capture()
        if cap is None:
            messagebox.showerror("Error", "Cannot open webcam!")
            return
        while True:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_classifier.detectMultiScale(gray, 1.3, 5)
            for (x,y,w,h) in faces:
                roi = cv2.resize(gray[y:y+h, x:x+w], (200,200))
                id, conf = self.model.predict(roi)
                if conf < 65:
                    name = names[id].upper()
                    self.save_to_csv(name)
                    cv2.putText(frame, f"{name} PRESENT", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                else:
                    cv2.putText(frame, "UNKNOWN", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                cv2.rectangle(frame, (x,y), (x+w, y+h), (255,255,255), 2)
            cv2.imshow("Attendance Mode (ESC to exit)", frame)
            if cv2.waitKey(1) == 27: break
        cap.release()
        cv2.destroyAllWindows()

    def save_to_csv(self, name):
        header = ["Name", "Time", "Date"]
        today = datetime.now().strftime("%d-%m-%Y")
        if not os.path.exists('attendance.csv') or os.stat('attendance.csv').st_size == 0:
            pd.DataFrame(columns=header).to_csv('attendance.csv', index=False)
        
        df = pd.read_csv('attendance.csv')
        if not ((df['Name'] == name) & (df['Date'] == today)).any():
            new_row = pd.DataFrame([[name, datetime.now().strftime('%H:%M:%S'), today]], columns=header)
            new_row.to_csv('attendance.csv', mode='a', header=False, index=False)

    def view_attendance(self):
        if os.path.exists('attendance.csv'):
            os.startfile('attendance.csv')

    def search_stats(self):
        sw = tk.Toplevel(self.root)
        sw.title("Search Statistics")
        sw.geometry("400x300")
        tk.Label(sw, text="Student Name:").pack(pady=10)
        s_var = tk.StringVar()
        tk.Entry(sw, textvariable=s_var).pack()

        def find():
            name = s_var.get().upper()
            if not os.path.exists('attendance.csv'): return
            df = pd.read_csv('attendance.csv')
            res = df[df['Name'] == name]
            messagebox.showinfo("Stats", f"Student: {name}\nTotal Attendance: {len(res)}")

        tk.Button(sw, text="Search", command=find, bg="#8e44ad", fg="white").pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceSystem(root)
    root.mainloop()
    
    
    
    # & "C:\Users\Sharukh\AppData\Local\Programs\Python\Python314\python.exe" attendance_sys.py