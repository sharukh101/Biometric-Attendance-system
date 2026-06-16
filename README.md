# Biometric Attendance System

A lightweight biometric attendance system that captures user attendance using face recognition (or fingerprint) and records it in a CSV-based backend. This project combines a simple web interface with a Python backend to demonstrate an end-to-end biometric attendance flow suitable for small labs, classrooms, or demo environments.


![Biometric fingerprint](https://upload.wikimedia.org/wikipedia/commons/9/9b/Fingerprint.svg)

## Key Features
- Register and recognize users using biometric data (face/fingerprint).
- Stores attendance records in CSV files (attendance.csv) for easy export.
- Simple web UI to view and trigger attendance operations.
- Minimal dependencies and easy to run locally or deploy to simple hosting (e.g., Vercel for front-end + Python backend on a small VM).


## Working flow
1. User registration
   - The system captures biometric data (face image or fingerprint template) for a new user and maps it to a unique student record (ID, name).
   - The user data is saved to the students.csv dataset and biometric templates are stored/managed by the Python backend.

2. Recognition / Check-in
   - When a user arrives, the system captures live biometric input (camera frame or fingerprint scan).
   - The backend compares the live sample against stored templates using the chosen recognition algorithm.
   - If a match is found, the system logs a timestamped attendance entry in attendance.csv for that student.

3. Review
   - The web UI (index.html + static assets) provides a quick view of recorded attendance and simple controls for testing recognition and registration.


![System flowchart](https://upload.wikimedia.org/wikipedia/commons/6/6b/Flow_chart.svg)

## Tools & Technologies used
- Python 3.x — backend logic and recognition pipeline (web_app.py and attendance_sys.py).
- Flask or a lightweight HTTP server (built into web_app.py) — serves the frontend and handles API routes.
- OpenCV / face-recognition libraries or fingerprint SDKs — capture and compare biometric samples (check requirements in requirements.txt).
- HTML/CSS/JavaScript — simple frontend (index.html) for interacting with the system.
- CSV files (students.csv, attendance.csv) — persistent storage for demo/demo-scale projects.
- Vercel configuration (vercel.json) — example configuration included for front-end hosting.


## Project structure
- index.html — front-end UI
- web_app.py — Flask-like web server, API endpoints, and integration code
- attendance_sys.py — core attendance and recognition logic
- students.csv — list of registered students
- attendance.csv — attendance logs (timestamped)
- static/ — static assets (images, css, js)
- templates/ — HTML templates (if used)
- requirements.txt — Python dependencies


## Installation & Quick Start
1. Create a Python 3 virtual environment and activate it:

   python3 -m venv venv
   source venv/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

3. Run the web app locally:

   python web_app.py

4. Open the UI:

   Open `index.html` in a browser or navigate to the local server address (by default http://127.0.0.1:5000 if using Flask).

5. Register a user and test recognition using your webcam or an attached biometric sensor. Attendance entries will be appended to `attendance.csv`.


## Notes & Customization
- For production usage you should replace CSV storage with a proper database (SQLite/Postgres) and secure the biometric templates and transport (HTTPS, encryption).
- Replace the simple recognition code with a robust SDK or ML model for higher accuracy and security.
- Add authentication for the web interface if multiple administrators will access it.


![App screenshot placeholder](https://upload.wikimedia.org/wikipedia/commons/3/3c/Monitoring_Screen.svg)

## Contributing
Contributions, bug reports, and feature requests are welcome — open an issue or submit a PR.

## License
This repository does not include a license file. Add a LICENSE if you intend to make the project open source.
