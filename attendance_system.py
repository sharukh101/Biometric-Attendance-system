# import cv2
# import os
# import numpy as np
# from datetime import datetime

# # Setup paths
# data_path = 'training_images/'
# if not os.path.exists(data_path):
#     os.makedirs(data_path)

# # 1. Face Detector aur Recognizer
# face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
# model = cv2.face.LBPHFaceRecognizer_create()

# def train_model():
#     training_data, labels = [], []
#     files = [f for f in os.listdir(data_path) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
#     if not files:
#         print("❌ ERROR: 'training_images' folder khali hai! Isme apni photos daalein.")
#         return None

#     print("🔍 Status: Extracting faces and Training...")
#     valid_filenames = []
    
#     for i, file in enumerate(files):
#         img_path = os.path.join(data_path, file)
#         img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        
#         if img is None: continue

#         # Photo mein chehra dhundhna
#         faces = face_classifier.detectMultiScale(img, 1.3, 5)
        
#         if len(faces) == 0:
#             print(f"⚠️ Warning: Image '{file}' mein chehra nahi mila. Is photo ko skip kar rahe hain.")
#             continue

#         for (x, y, w, h) in faces:
#             face_roi = cv2.resize(img[y:y+h, x:x+w], (200, 200))
#             training_data.append(np.asarray(face_roi, dtype=np.uint8))
#             labels.append(len(valid_filenames)) 
#             valid_filenames.append(file)
#             break 
            
#     if len(training_data) == 0:
#         print("❌ CRITICAL ERROR: Kisi bhi photo mein face nahi mila. Train nahi ho sakta!")
#         return None
        
#     model.train(np.asarray(training_data), np.asarray(labels))
#     print(f"✅ Success: {len(training_data)} photos par model train ho gaya!")
#     return valid_filenames

# filenames = train_model()

# # Agar training fail hui toh project stop kar do
# if filenames is None:
#     print("System setup failed. Please check your training images.")
#     exit()

# def markAttendance(name):
#     if not os.path.exists('attendance.csv'):
#         with open('attendance.csv', 'w') as f:
#             f.write("Name,Time,Date\n")

#     with open('attendance.csv', 'r+') as f:
#         lines = f.readlines()
#         names = [line.split(',')[0] for line in lines]
#         if name not in names:
#             now = datetime.now()
#             f.writelines(f'{name},{now.strftime("%H:%M:%S")},{now.strftime("%d-%m-%Y")}\n')
#             print(f"✅ Attendance Recorded: {name}")

# print("🚀 System Starting... Press 'Enter' in camera window to Exit.")
# cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# while True:
#     ret, frame = cap.read()
#     if not ret: break
    
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = face_classifier.detectMultiScale(gray, 1.3, 5)

#     for (x, y, w, h) in faces:
#         face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
#         id, confidence = model.predict(face_roi)
        
#         # Confidence score print for debugging
#         # print(f"Score: {confidence}") 

#         # Strict Threshold (Ise 50 se 65 ke beech rakhein)
#         if confidence < 60: 
#             name = os.path.splitext(filenames[id])[0].upper()
#             # Agar file ka naam 'Unknown' se start hota hai toh use unknown dikhao
#             if "UNKNOWN" in name:
#                 name = "UNKNOWN"
#                 color = (0, 0, 255)
#             else:
#                 color = (0, 255, 0)
#                 markAttendance(name)
#         else:
#             name = "UNKNOWN"
#             color = (0, 0, 255)
        
#         cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
#         cv2.putText(frame, f"{name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

#     cv2.rectangle(frame, (0,0), (640, 40), (50,50,50), -1)
#     cv2.putText(frame, "COLLEGE PROJECT: FACE ATTENDANCE", (120, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    
#     cv2.imshow('Face Recognition System', frame)
#     if cv2.waitKey(1) == 13: break

# cap.release()
# cv2.destroyAllWindows()
