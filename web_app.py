import os
import csv
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for the static frontend served via Go Live on port 5500
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Data Storage Paths
STUDENTS_CSV = "students.csv"
ATTENDANCE_CSV = "attendance.csv"
DESCRIPTORS_JSON = "students_descriptors.json"
PHOTOS_DIR = os.path.join("static", "registered_faces")

# Ensure storage environment directories and files exist
if not os.path.exists(PHOTOS_DIR):
    os.makedirs(PHOTOS_DIR)

if not os.path.exists(STUDENTS_CSV):
    with open(STUDENTS_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Email", "Class"])

if not os.path.exists(ATTENDANCE_CSV):
    with open(ATTENDANCE_CSV, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Date", "Time"])

def load_descriptors():
    if os.path.exists(DESCRIPTORS_JSON):
        try:
            with open(DESCRIPTORS_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_descriptors(data):
    with open(DESCRIPTORS_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_students = 0
    if os.path.exists(STUDENTS_CSV):
        try:
            with open(STUDENTS_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                total_students = sum(1 for row in reader)
        except Exception as e:
            print("Error reading students CSV:", e)

    marked_today = 0
    today_str = datetime.now().strftime("%d-%m-%Y")
    if os.path.exists(ATTENDANCE_CSV):
        try:
            with open(ATTENDANCE_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Date") == today_str:
                        marked_today += 1
        except Exception as e:
            print("Error reading attendance CSV:", e)

    return jsonify({
        "total_students": total_students,
        "marked_today": marked_today
    })

@app.route('/api/students', methods=['GET'])
def get_students():
    students = []
    descriptors_dict = load_descriptors()
    
    if os.path.exists(STUDENTS_CSV):
        try:
            with open(STUDENTS_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["Name"]
                    email = row["Email"]
                    class_name = row["Class"]
                    
                    student_data = descriptors_dict.get(name, {})
                    
                    # Read base64 image strings from saved files
                    img_urls = []
                    for i in range(1, 4):
                        filename = f"{name.replace(' ', '_')}_{i}.jpg"
                        filepath = os.path.join(PHOTOS_DIR, filename)
                        if os.path.exists(filepath):
                            try:
                                with open(filepath, "rb") as img_file:
                                    base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                                    img_urls.append(f"data:image/jpeg;base64,{base64_str}")
                            except Exception:
                                pass
                    
                    students.append({
                        "name": name,
                        "email": email,
                        "class_name": class_name,
                        "descriptors": student_data.get("descriptors", []),
                        "images": img_urls
                    })
        except Exception as e:
            print("Error fetching students:", e)
            
    return jsonify(students)

@app.route('/api/attendance_records', methods=['GET'])
def get_attendance():
    records = []
    if os.path.exists(ATTENDANCE_CSV):
        try:
            with open(ATTENDANCE_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append({
                        "Name": row.get("Name"),
                        "Date": row.get("Date"),
                        "Time": row.get("Time")
                    })
        except Exception as e:
            print("Error reading attendance CSV:", e)
    return jsonify(records)

@app.route('/api/register_student', methods=['POST'])
def register_student():
    data = request.get_json() or {}
    name = data.get("name", "").strip().upper()
    email = data.get("email", "").strip()
    class_name = data.get("class_name", "").strip().upper()
    descriptors = data.get("descriptors", [])
    images = data.get("images", [])

    if not name or not email or not class_name:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        # 1. Update CSV database
        rows = []
        if os.path.exists(STUDENTS_CSV):
            with open(STUDENTS_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        
        header = rows[0] if rows else ["Name", "Email", "Class"]
        rows = [row for row in rows[1:] if row[0] != name]
        rows.insert(0, header)
        rows.append([name, email, class_name])
        
        with open(STUDENTS_CSV, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # 2. Save face descriptors
        descriptors_dict = load_descriptors()
        descriptors_dict[name] = {
            "email": email,
            "class_name": class_name,
            "descriptors": descriptors
        }
        save_descriptors(descriptors_dict)

        # 3. Save images to local static directory
        for i, img_data_url in enumerate(images):
            if ',' in img_data_url:
                base64_data = img_data_url.split(',')[1]
                img_bytes = base64.b64decode(base64_data)
                
                filename = f"{name.replace(' ', '_')}_{i+1}.jpg"
                filepath = os.path.join(PHOTOS_DIR, filename)
                with open(filepath, "wb") as img_file:
                    img_file.write(img_bytes)

        return jsonify({"success": True, "message": f"Successfully registered student {name}"})
    except Exception as e:
        print("Registration error:", e)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json() or {}
    name = data.get("name", "").strip().upper()
    
    if not name:
        return jsonify({"success": False, "message": "Name is required"}), 400

    today = datetime.now().strftime("%d-%m-%Y")
    time_str = datetime.now().strftime("%H:%M:%S")

    try:
        already_logged = False
        if os.path.exists(ATTENDANCE_CSV):
            with open(ATTENDANCE_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Name") == name and row.get("Date") == today:
                        already_logged = True
                        break
        
        if not already_logged:
            with open(ATTENDANCE_CSV, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([name, today, time_str])
            return jsonify({"success": True, "message": f"Attendance marked for {name}"})
        else:
            return jsonify({"success": True, "message": f"Attendance already marked today for {name}"})
    except Exception as e:
        print("Error logging attendance:", e)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/delete_student', methods=['POST'])
def delete_student():
    data = request.get_json() or {}
    name = data.get("name", "").strip().upper()
    
    if not name:
        return jsonify({"success": False, "message": "Name is required"}), 400

    try:
        # 1. Update CSV database
        rows = []
        if os.path.exists(STUDENTS_CSV):
            with open(STUDENTS_CSV, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
        
        header = rows[0] if rows else ["Name", "Email", "Class"]
        rows = [row for row in rows[1:] if row[0] != name]
        rows.insert(0, header)
        
        with open(STUDENTS_CSV, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # 2. Update descriptors JSON
        descriptors_dict = load_descriptors()
        if name in descriptors_dict:
            del descriptors_dict[name]
        save_descriptors(descriptors_dict)

        # 3. Delete physical image files from disk
        for i in range(1, 4):
            filename = f"{name.replace(' ', '_')}_{i}.jpg"
            filepath = os.path.join(PHOTOS_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        return jsonify({"success": True, "message": f"Deleted student {name}"})
    except Exception as e:
        print("Error deleting student:", e)
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_file('index.html')

@app.route('/students_list.html')
def serve_students_list():
    return send_file('students_list.html')

if __name__ == '__main__':
    # Start flask application on local port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
