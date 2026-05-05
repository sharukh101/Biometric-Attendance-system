import cv2
import os
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import pandas as pd

# Setup Directories
if not os.path.exists('training_images'): os.makedirs('training_images')

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
        reg_win.geometry("300x200")
        tk.Label(reg_win, text="Enter Student Name:").pack(pady=10)
        name_var = tk.StringVar()
        tk.Entry(reg_win, textvariable=name_var).pack()

        def capture():
            name = name_var.get().upper()
            if not name: 
                messagebox.showerror("Error", "Please enter a name!")
                return
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            count = 0
            while count < 5:
                ret, frame = cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_classifier.detectMultiScale(gray, 1.3, 5)
                for (x,y,w,h) in faces:
                    count += 1
                    cv2.imwrite(f"training_images/{name}_{count}.jpg", gray[y:y+h, x:x+w])
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
                cv2.imshow("Registering...", frame)
                if cv2.waitKey(1) == 27: break
            cap.release()
            cv2.destroyAllWindows()
            messagebox.showinfo("Success", f"Registered {name}")
            reg_win.destroy()

        tk.Button(reg_win, text="Start Capture", command=capture).pack(pady=20)

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
            names.append(f.split('_')[0])

        self.model.train(np.asarray(training_data), np.asarray(labels))
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
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