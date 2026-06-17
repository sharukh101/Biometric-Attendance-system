/* ==========================================================================
   ADVANCED AI ATTENDANCE SYSTEM - FRONTEND INTERACTIVE ENGINE (WITH PYTHON BACKEND INLINE)
   ========================================================================== */

// Global State
const API_BASE = "http://127.0.0.1:5000";
let globalRecords = [];
let modelsLoaded = false;
let activeCameraStream = null;
let regLoopActive = false;
let scanLoopActive = false;
let faceMatcher = null;
let capturedDescriptors = []; // Holds 3 Float32Array descriptors for registration
let capturedImages = [];      // Holds 3 cropped Base64 face images for registration
let registrationStep = 1;

// Public jsDelivr CDN model weight endpoints (with fallbacks)
const MODEL_URLS = [
    'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/',
    'https://justadudewhohacks.github.io/face-api.js/models'
];

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Local Storage Databases if they don't exist
    if (!localStorage.getItem('students')) {
        localStorage.setItem('students', JSON.stringify([]));
    }
    if (!localStorage.getItem('attendance')) {
        localStorage.setItem('attendance', JSON.stringify([]));
    }

    // 1. Initialize Clock
    startLiveClock();

    // 2. Initialize Navigation Tabs
    initNavigation();

    // 3. Bind Registration Controls
    initRegistration();

    // 4. Bind Camera Stream Controls
    initCameraScanner();

    // 5. Bind Records Filters and Actions
    initRecordsDatabase();

    // 6. Initialize Theme Toggle
    initThemeToggle();

    // 7. Update status indicator to pending
    updateStatusIndicator("AI Initializing...", "pending");

    // 8. Pre-load face-api models in the background
    await loadModelsBackground();

    // 9. Synchronize with Python Flask Backend if online
    await syncWithBackend();

    // 10. Restore active tab or default to dashboard
    const savedTab = localStorage.getItem('activeTab') || 'tab-dashboard';
    switchTab(savedTab);
});

/* ==========================================================================
   BACKEND SYNCHRONIZATION UTILITY
   ========================================================================== */
async function syncWithBackend() {
    try {
        // Try fetching registered students from Flask server
        const res = await fetch(`${API_BASE}/api/students`);
        if (res.ok) {
            const backendStudents = await res.json();
            localStorage.setItem('students', JSON.stringify(backendStudents));
        }

        // Try fetching attendance logs from Flask server
        const res2 = await fetch(`${API_BASE}/api/attendance_records`);
        if (res2.ok) {
            const backendAttendance = await res2.json();
            localStorage.setItem('attendance', JSON.stringify(backendAttendance));
        }
        
        updateStatusIndicator("AI Engine Ready (Connected)", "success");
        console.log("Synchronized successfully with Python Flask backend.");
    } catch (err) {
        console.warn("Python backend offline. Running in Local Storage Mode.");
        updateStatusIndicator("AI Engine Ready (Local)", "success");
    }
}

/* ==========================================================================
   STATUS INDICATOR HELPER
   ========================================================================== */
function updateStatusIndicator(text, state) {
    const textEl = document.querySelector('.status-indicator .status-text');
    const dotEl = document.querySelector('.status-indicator .pulse-dot');
    if (!textEl || !dotEl) return;
    
    textEl.textContent = text;
    dotEl.style.animation = 'none'; // Stop current CSS animation
    
    if (state === 'success') {
        dotEl.style.backgroundColor = 'hsl(var(--accent-green))';
        dotEl.style.boxShadow = '0 0 10px hsl(var(--accent-green))';
        dotEl.style.animation = 'pulse 1.8s infinite';
    } else if (state === 'pending') {
        dotEl.style.backgroundColor = 'hsl(var(--accent-blue))';
        dotEl.style.boxShadow = '0 0 10px hsl(var(--accent-blue))';
        dotEl.style.animation = 'pulse 1.8s infinite';
    } else if (state === 'error') {
        dotEl.style.backgroundColor = 'hsl(var(--accent-red))';
        dotEl.style.boxShadow = '0 0 10px hsl(var(--accent-red))';
        dotEl.style.animation = 'none';
    } else {
        dotEl.style.backgroundColor = 'hsl(var(--text-muted))';
        dotEl.style.boxShadow = 'none';
        dotEl.style.animation = 'none';
    }
}

/* ==========================================================================
   MODEL LOADER (WITH CDN FALLBACK)
   ========================================================================== */
async function loadModels(logFn = console.log) {
    if (modelsLoaded) return;
    
    // Attempt loading from preferred URL, fallback to secondary if failure occurs
    for (let i = 0; i < MODEL_URLS.length; i++) {
        const url = MODEL_URLS[i];
        logFn(`[SYSTEM] Loading AI models from CDN source ${i + 1}...`);
        try {
            await faceapi.nets.ssdMobilenetv1.loadFromUri(url);
            await faceapi.nets.faceLandmark68Net.loadFromUri(url);
            await faceapi.nets.faceRecognitionNet.loadFromUri(url);
            modelsLoaded = true;
            logFn("[SYSTEM] AI models loaded successfully!");
            return;
        } catch (err) {
            console.warn(`Failed loading models from ${url}:`, err);
            if (i === MODEL_URLS.length - 1) {
                logFn("[ERROR] Failed to load AI models from all sources. Please check internet connection.");
                throw err;
            }
        }
    }
}

async function loadModelsBackground() {
    try {
        await loadModels();
    } catch (err) {
        updateStatusIndicator("AI Load Error", "error");
    }
}

/* ==========================================================================
   WEBCAM HELPER UTILITIES
   ========================================================================== */
async function startWebcam(videoElement) {
    if (activeCameraStream) {
        stopWebcam();
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Webcam access requires a secure context (HTTPS or localhost/127.0.0.1). Please launch the project using VS Code's 'Go Live' server or Python Flask server, rather than opening the HTML file directly as a local file.");
    }
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            }
        });
        videoElement.srcObject = stream;
        activeCameraStream = stream;
        return stream;
    } catch (err) {
        console.error("Camera access failed:", err);
        throw err;
    }
}

function stopWebcam() {
    if (activeCameraStream) {
        activeCameraStream.getTracks().forEach(track => track.stop());
        activeCameraStream = null;
    }
}

/* ==========================================================================
   WIDGET: LIVE CLOCK & CALENDAR
   ========================================================================== */
function startLiveClock() {
    const clockElement = document.getElementById('live-clock');
    if (!clockElement) return;
    
    function tick() {
        const now = new Date();
        
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        const hoursStr = String(hours).padStart(2, '0');
        
        // Date Formatting
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        
        clockElement.textContent = `${hoursStr}:${minutes}:${seconds} ${ampm} | ${day}-${month}-${year}`;
    }
    
    tick();
    setInterval(tick, 1000);
}

/* ==========================================================================
   ROUTING: SINGLE PAGE TAB NAVIGATION
   ========================================================================== */
function initNavigation() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });
}

async function switchTab(tabId) {
    // Deactivate all menu items
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-tab') === tabId) {
            item.classList.add('active');
        }
    });

    // Toggle panels
    const panels = document.querySelectorAll('.tab-panel');
    panels.forEach(panel => {
        panel.classList.remove('active');
    });

    const activePanel = document.getElementById(tabId);
    if (activePanel) {
        activePanel.classList.add('active');
    }

    // Persist active tab to localStorage
    localStorage.setItem('activeTab', tabId);

    // Stop loops when leaving active webcam views
    if (tabId !== 'tab-register' && regLoopActive) {
        const btnToggleCam = document.getElementById('btn-toggle-reg-camera');
        if (btnToggleCam) btnToggleCam.click(); // Programmatically stop registration webcam stream
    }
    if (tabId !== 'tab-attendance' && scanLoopActive) {
        const btnStop = document.getElementById('btn-stop-scanning');
        if (btnStop) btnStop.click(); // Programmatically stop attendance webcam stream
    }

    // Sync database state with backend when loading views
    await syncWithBackend();

    // Update Topbar Title Header
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
        switch (tabId) {
            case 'tab-dashboard':
                pageTitle.textContent = "Dashboard Overview";
                loadDashboardData();
                break;
            case 'tab-register':
                pageTitle.textContent = "Register Student Face";
                break;
            case 'tab-attendance':
                pageTitle.textContent = "Live Attendance Scanner";
                loadTimelineLogs();
                break;
            case 'tab-records':
                pageTitle.textContent = "Logs & Attendance Database";
                loadFullAttendanceRecords();
                break;
        }
    }
}

/* ==========================================================================
   TAB 1: DASHBOARD ENGINE
   ========================================================================== */
function loadDashboardData() {
    const students = JSON.parse(localStorage.getItem('students')) || [];
    const attendance = JSON.parse(localStorage.getItem('attendance')) || [];
    
    // Calculate today's marked attendance
    const today = getTodayFormattedString();
    const todayAttendanceCount = attendance.filter(log => log.Date === today).length;

    // Load general counts
    document.getElementById('stat-total-students').textContent = students.length;
    document.getElementById('stat-marked-today').textContent = todayAttendanceCount;
    
    const scannerStatus = document.getElementById('stat-scanner-status');
    if (scannerStatus) {
        if (scanLoopActive) {
            scannerStatus.textContent = "Scanning Live";
            scannerStatus.parentElement.parentElement.className = "stats-card card-glow-green";
        } else {
            scannerStatus.textContent = "Offline";
            scannerStatus.parentElement.parentElement.className = "stats-card card-glow-blue";
        }
    }

    // Load registered students list (pills)
    const listContainer = document.getElementById('dashboard-student-list');
    if (listContainer) {
        listContainer.innerHTML = '';
        
        if (students.length === 0) {
            listContainer.innerHTML = '<div class="no-records">No students registered yet.</div>';
        } else {
            students.forEach(student => {
                const pill = document.createElement('div');
                pill.className = 'student-pill animate-fade';
                pill.textContent = student.name;
                listContainer.appendChild(pill);
            });
        }
    }

    // Load compact activity log (recent 5 logs)
    const tbody = document.querySelector('#table-recent-attendance tbody');
    if (tbody) {
        tbody.innerHTML = '';
        
        if (attendance.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="no-records">No attendance logged yet.</td></tr>';
        } else {
            // Sort attendance with newest logged at the top
            const sortedRecords = [...attendance].reverse();
            const recent = sortedRecords.slice(0, 5);
            recent.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:600; text-transform: uppercase;">${row.Name}</td>
                    <td>${row.Date}</td>
                    <td style="font-family: monospace; color: var(--accent-green); font-weight:600;">${row.Time}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
}

/* ==========================================================================
   TAB 2: STUDENT REGISTRATION ENGINE
   ========================================================================== */
function initRegistration() {
    const input = document.getElementById('reg-student-name');
    const inputEmail = document.getElementById('reg-student-email');
    const inputClass = document.getElementById('reg-student-class');
    const btnToggleCam = document.getElementById('btn-toggle-reg-camera');
    const btnCapture = document.getElementById('btn-capture-photo');
    const btnConfirm = document.getElementById('btn-confirm-register');
    const logBox = document.getElementById('register-log');
    
    // Prevent default form submission reload when pressing Enter in input fields
    [input, inputEmail, inputClass].forEach(inp => {
        if (inp) {
            inp.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                }
            });
        }
    });
    
    const container = document.getElementById('reg-camera-screen-container');
    const videoFeed = document.getElementById('reg-camera-feed');
    const canvasOverlay = document.getElementById('reg-camera-canvas');
    const placeholder = document.getElementById('reg-camera-placeholder');

    function addLog(text, styleClass = '') {
        if (!logBox) return;
        const line = document.createElement('div');
        line.className = `log-line ${styleClass}`;
        
        // Get dynamic time label
        const now = new Date();
        const timeLabel = `[${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}]`;
        
        line.textContent = `${timeLabel} ${text}`;
        logBox.appendChild(line);
        logBox.scrollTop = logBox.scrollHeight;
    }

    btnToggleCam.addEventListener('click', async () => {
        if (!regLoopActive) {
            const name = input.value.trim().toUpperCase();
            const email = inputEmail.value.trim();
            const className = inputClass.value.trim().toUpperCase();
            if (!name || !email || !className) {
                addLog('[ERROR] Name, Email, and Class/Semester are all compulsory before starting registration!', 'error');
                return;
            }
            
            // Check if name is already registered
            const students = JSON.parse(localStorage.getItem('students')) || [];
            const exists = students.some(s => s.name === name);
            if (exists) {
                addLog(`[WARNING] Student '${name}' is already registered. Re-registering will overwrite their existing face data.`, 'highlight');
            }

            await startRegCamera(name);
        } else {
            stopRegCamera();
        }
    });

    btnCapture.addEventListener('click', async () => {
        const name = input.value.trim().toUpperCase();
        if (!name) return;
        await captureSingleStep(name);
    });

    btnConfirm.addEventListener('click', async () => {
        const name = input.value.trim().toUpperCase();
        const email = inputEmail.value.trim();
        const className = inputClass.value.trim().toUpperCase();
        
        if (!name || !email || !className) {
            addLog('[ERROR] All fields (Name, Email, Class) are compulsory!', 'error');
            return;
        }
        if (capturedDescriptors.length < 3) {
            addLog('[ERROR] Missing facial descriptors. Capture all 3 angles first!', 'error');
            return;
        }

        btnConfirm.disabled = true;
        addLog(`[SYSTEM] Finalizing registration and storing profiles...`, 'highlight');

        try {
            const newStudent = {
                name: name,
                email: email,
                class_name: className,
                descriptors: capturedDescriptors,
                images: capturedImages
            };

            // 1. Save to Python Flask backend
            let savedOnBackend = false;
            try {
                const response = await fetch(`${API_BASE}/api/register_student`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newStudent)
                });
                if (response.ok) {
                    savedOnBackend = true;
                    addLog(`[PYTHON] Profile successfully saved to students.csv!`, 'success');
                    addLog(`[PYTHON] Facial JPEGs written inside static/registered_faces/!`, 'success');
                }
            } catch (backendErr) {
                console.warn("Backend offline. Saving in Local Storage Mode.", backendErr);
            }

            // 2. Sync client-side fallback
            let students = JSON.parse(localStorage.getItem('students')) || [];
            students = students.filter(s => s.name !== name);
            students.push(newStudent);
            localStorage.setItem('students', JSON.stringify(students));
            
            if (!savedOnBackend) {
                addLog(`[WARNING] Backend server offline. Registered locally in browser storage.`, 'highlight');
            }

            addLog(`[SUCCESS] Registered '${name}' in database successfully!`, 'success');
            showToast('Registered Successfully', `'${name}' has been enrolled in the database.`);
            
            // Clear fields and close camera
            input.value = '';
            inputEmail.value = '';
            inputClass.value = '';
            stopRegCamera();
            
            await syncWithBackend();
            loadDashboardData();
        } catch (err) {
            btnConfirm.disabled = false;
            addLog(`[ERROR] Registration failed: ${err.message}`, 'error');
        }
    });

    async function startRegCamera(name) {
        input.disabled = true;
        inputEmail.disabled = true;
        inputClass.disabled = true;
        registrationStep = 1;
        capturedDescriptors = [];
        capturedImages = [];
        
        logBox.innerHTML = ''; // Reset logs
        addLog('[CAMERA] Starting camera preview feed...');
        
        // Ensure models are loaded
        if (!modelsLoaded) {
            updateStatusIndicator("AI Initializing...", "pending");
            try {
                await loadModels(text => addLog(text, 'highlight'));
                await syncWithBackend();
            } catch (modelErr) {
                updateStatusIndicator("AI Load Error", "error");
                addLog(`[ERROR] AI models loading failed: ${modelErr.message}. Check your internet connection.`, 'error');
                input.disabled = false;
                inputEmail.disabled = false;
                inputClass.disabled = false;
                stopRegCamera();
                return;
            }
        }
        
        // Initialize Webcam
        try {
            await startWebcam(videoFeed);
        } catch (camErr) {
            updateStatusIndicator("Camera Error", "error");
            addLog(`[ERROR] Webcam access denied or failed: ${camErr.message}`, 'error');
            input.disabled = false;
            inputEmail.disabled = false;
            inputClass.disabled = false;
            stopRegCamera();
            return;
        }

        try {
            // UI Visual States
            placeholder.style.display = 'none';
            videoFeed.style.display = 'block';
            canvasOverlay.style.display = 'block';
            container.classList.add('streaming');
            
            regLoopActive = true;
            runRegistrationLoop();
            
            btnToggleCam.innerHTML = `
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="9" y1="9" x2="15" y2="15"/>
                    <line x1="15" y1="9" x2="9" y2="15"/>
                </svg>
                Close Camera Preview
            `;
            btnToggleCam.className = "btn btn-danger";
            
            // Setup capture button
            btnCapture.style.display = 'inline-flex';
            btnCapture.disabled = false;
            btnCapture.innerHTML = `
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="3"/>
                </svg>
                Capture Snapshot (1/3) - Look Straight
            `;
            
            // Setup register button
            btnConfirm.style.display = 'inline-flex';
            btnConfirm.disabled = true;
            
            addLog('[CAMERA] Webcam viewfinder turned online successfully.');
            addLog('[SYSTEM] Please look straight at the camera and click "Capture Snapshot (1/3)" to begin.', 'highlight');
        } catch (err) {
            addLog(`[ERROR] Registration startup failed: ${err.message}`, 'error');
            input.disabled = false;
            inputEmail.disabled = false;
            inputClass.disabled = false;
            stopRegCamera();
        }
    }

    function stopRegCamera() {
        regLoopActive = false;
        stopWebcam();
        
        // Reset Video / Canvas View
        videoFeed.srcObject = null;
        videoFeed.style.display = 'none';
        canvasOverlay.style.display = 'none';
        const ctx = canvasOverlay.getContext('2d');
        ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
        
        placeholder.style.display = 'flex';
        container.classList.remove('streaming');
        
        // Reset form inputs
        input.disabled = false;
        inputEmail.disabled = false;
        inputClass.disabled = false;
        
        // Reset action buttons
        btnToggleCam.innerHTML = `
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
            </svg>
            Open Camera & Register Face
        `;
        btnToggleCam.className = "btn btn-primary btn-glow-purple";
        
        btnCapture.style.display = 'none';
        btnConfirm.style.display = 'none';
        
        addLog('[SYSTEM] Camera closed. Face registration standby.');
    }

    async function runRegistrationLoop() {
        if (!regLoopActive || !activeCameraStream) return;
        
        if (videoFeed.paused || videoFeed.ended || videoFeed.offsetWidth === 0) {
            requestAnimationFrame(runRegistrationLoop);
            return;
        }
        
        try {
            const displaySize = { width: videoFeed.offsetWidth, height: videoFeed.offsetHeight };
            faceapi.matchDimensions(canvasOverlay, displaySize);
            
            // Fast single face detection for visual feedback
            const detection = await faceapi.detectSingleFace(videoFeed, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.5 }))
                                              .withFaceLandmarks();
            
            const ctx = canvasOverlay.getContext('2d');
            ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
            
            if (detection) {
                const resizedDetections = faceapi.resizeResults(detection, displaySize);
                faceapi.draw.drawDetections(canvasOverlay, resizedDetections);
            }
        } catch (err) {
            console.error("Error in registration visualization frame:", err);
        }
        
        requestAnimationFrame(runRegistrationLoop);
    }

    async function captureSingleStep(name) {
        if (!regLoopActive) return;
        
        let step = registrationStep;
        let ordinal = step === 1 ? "1st" : (step === 2 ? "2nd" : "3rd");
        let angleDesc = step === 1 ? "Look Straight" : (step === 2 ? "Turn Left" : "Turn Right");
        
        btnCapture.disabled = true;
        btnToggleCam.disabled = true;
        addLog(`[SYSTEM] Capturing ${ordinal} snapshot (${angleDesc}). Processing details...`, 'highlight');
        
        try {
            // Detect face descriptor in current stream frame
            const detection = await faceapi.detectSingleFace(videoFeed)
                                              .withFaceLandmarks()
                                              .withFaceDescriptor();
                                              
            if (!detection) {
                addLog(`[ERROR] No face detected! Look directly at the camera at a proper angle and click capture again.`, 'error');
                btnCapture.disabled = false;
                btnToggleCam.disabled = false;
                return;
            }
            
            // Crop face image and convert to low-res base64 to save local storage space
            try {
                const box = detection.detection.box;
                const faceCanvas = document.createElement('canvas');
                faceCanvas.width = 150;
                faceCanvas.height = 150;
                const faceCtx = faceCanvas.getContext('2d');
                
                // Draw cropped face from video frame
                faceCtx.drawImage(
                    videoFeed,
                    box.x, box.y, box.width, box.height,
                    0, 0, 150, 150
                );
                const faceDataUrl = faceCanvas.toDataURL('image/jpeg', 0.75); // quality 0.75 is very lightweight
                capturedImages.push(faceDataUrl);
            } catch (cropErr) {
                console.warn("Face crop failed, fallback to full video frame:", cropErr);
                // Fallback to taking a small version of the entire frame
                const faceCanvas = document.createElement('canvas');
                faceCanvas.width = 150;
                faceCanvas.height = 112;
                const faceCtx = faceCanvas.getContext('2d');
                faceCtx.drawImage(videoFeed, 0, 0, 150, 112);
                capturedImages.push(faceCanvas.toDataURL('image/jpeg', 0.6));
            }
            
            // Store descriptor serialized as array of numbers
            const descArray = Array.from(detection.descriptor);
            capturedDescriptors.push(descArray);
            
            addLog(`[CAMERA] Snapshot ${step}/3 captured successfully!`, 'success');
            
            if (step === 3) {
                btnCapture.disabled = true;
                btnConfirm.disabled = false;
                btnToggleCam.disabled = false;
                
                btnCapture.innerHTML = `
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 8 8 12 12 16"/>
                        <line x1="16" y1="12" x2="8" y2="12"/>
                    </svg>
                    Snapshots Completed
                `;
                addLog('[SYSTEM] All 3 snapshots captured successfully! Click "Register" below to save this profile.', 'highlight');
            } else {
                registrationStep = step + 1;
                btnCapture.disabled = false;
                btnToggleCam.disabled = false;
                
                let nextAngle = registrationStep === 2 ? "Turn Left" : "Turn Right";
                btnCapture.innerHTML = `
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                    Capture Snapshot (${registrationStep}/3) - ${nextAngle}
                `;
                addLog(`[SYSTEM] Snapshot ${step}/3 captured! Turn face slightly ${registrationStep === 2 ? 'LEFT' : 'RIGHT'} and click "Capture".`, 'highlight');
            }
        } catch (err) {
            btnCapture.disabled = false;
            btnToggleCam.disabled = false;
            addLog(`[ERROR] Descriptor capture failed: ${err.message}`, 'error');
        }
    }
}

/* ==========================================================================
   TAB 3: WEBCAM ATTENDANCE SCANNER ENGINE
   ========================================================================== */
function initCameraScanner() {
    const btnStart = document.getElementById('btn-start-scanning');
    const btnStop = document.getElementById('btn-stop-scanning');
    const container = document.getElementById('camera-screen-container');
    const videoFeed = document.getElementById('camera-feed');
    const canvasOverlay = document.getElementById('camera-canvas');
    const placeholder = document.getElementById('camera-placeholder');

    btnStart.addEventListener('click', async () => {
        // Toggle scanner state
        btnStart.disabled = true;
        btnStop.disabled = false;
        
        placeholder.style.display = 'none';
        videoFeed.style.display = 'block';
        canvasOverlay.style.display = 'block';
        container.classList.add('streaming');
        
        // Ensure models are loaded
        if (!modelsLoaded) {
            updateStatusIndicator("AI Initializing...", "pending");
            try {
                await loadModels();
            } catch (modelErr) {
                btnStart.disabled = false;
                btnStop.disabled = true;
                placeholder.style.display = 'flex';
                videoFeed.style.display = 'none';
                canvasOverlay.style.display = 'none';
                container.classList.remove('streaming');
                updateStatusIndicator("AI Load Error", "error");
                showToast("AI Load Error", "Failed to load face detection models. Please check your internet connection.");
                return;
            }
        }
        await syncWithBackend();
        
        // Start Webcam
        try {
            await startWebcam(videoFeed);
        } catch (camErr) {
            btnStart.disabled = false;
            btnStop.disabled = true;
            placeholder.style.display = 'flex';
            videoFeed.style.display = 'none';
            canvasOverlay.style.display = 'none';
            container.classList.remove('streaming');
            updateStatusIndicator("Camera Error", "error");
            showToast("Camera Error", "Webcam access could not be acquired: " + camErr.message);
            return;
        }

        try {
            // Build FaceMatcher database from local storage descriptors
            const students = JSON.parse(localStorage.getItem('students')) || [];
            const labeledDescriptors = [];
            
            students.forEach(s => {
                if (s.descriptors && s.descriptors.length > 0) {
                    const floatDescs = s.descriptors.map(d => new Float32Array(d));
                    labeledDescriptors.push(new faceapi.LabeledFaceDescriptors(s.name, floatDescs));
                }
            });
            
            if (labeledDescriptors.length > 0) {
                // Initialize matcher with a threshold of 0.6
                faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, 0.6);
            } else {
                faceMatcher = null;
                showToast("No Face Data", "There are no students registered yet. Register someone first!", "badge-red");
            }
            
            scanLoopActive = true;
            runScanningLoop();
            
            loadTimelineLogs();
        } catch (err) {
            console.error("Scanning startup failed:", err);
            updateStatusIndicator("Scanning Error", "error");
            showToast("Scanning Error", "An error occurred starting the attendance scanner: " + err.message);
            stopScanner();
        }
    });

    btnStop.addEventListener('click', stopScanner);

    async function stopScanner() {
        scanLoopActive = false;
        stopWebcam();
        
        // Clear UI Viewport
        videoFeed.srcObject = null;
        videoFeed.style.display = 'none';
        canvasOverlay.style.display = 'none';
        const ctx = canvasOverlay.getContext('2d');
        ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
        
        placeholder.style.display = 'flex';
        container.classList.remove('streaming');
        
        btnStart.disabled = false;
        btnStop.disabled = true;
        
        await syncWithBackend();
        loadTimelineLogs(); // final reload
    }

    async function runScanningLoop() {
        if (!scanLoopActive || !activeCameraStream) return;
        
        if (videoFeed.paused || videoFeed.ended || videoFeed.offsetWidth === 0) {
            requestAnimationFrame(runScanningLoop);
            return;
        }
        
        try {
            const displaySize = { width: videoFeed.offsetWidth, height: videoFeed.offsetHeight };
            faceapi.matchDimensions(canvasOverlay, displaySize);
            
            // Detect all faces in scanner view with recognition descriptors
            const detections = await faceapi.detectAllFaces(videoFeed, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.5 }))
                                              .withFaceLandmarks()
                                              .withFaceDescriptors();
            
            const ctx = canvasOverlay.getContext('2d');
            ctx.clearRect(0, 0, canvasOverlay.width, canvasOverlay.height);
            
            if (detections && detections.length > 0) {
                const resizedDetections = faceapi.resizeResults(detections, displaySize);
                
                resizedDetections.forEach(detection => {
                    let label = "Unknown";
                    
                    if (faceMatcher) {
                        const bestMatch = faceMatcher.findBestMatch(detection.descriptor);
                        // format output display label
                        if (!bestMatch.label.includes("unknown")) {
                            label = `${bestMatch.label.toUpperCase()} (${Math.round((1 - bestMatch.distance) * 100)}% Match)`;
                            
                            // Log attendance (connected to Python and local fallback)
                            markAttendanceLocally(bestMatch.label);
                        } else {
                            label = "Unknown Face";
                        }
                    }
                    
                    // Render styled bounding box
                    const box = detection.detection.box;
                    const isUnknown = label.toLowerCase().includes("unknown");
                    const drawBox = new faceapi.draw.DrawBox(box, { 
                        label: label,
                        boxColor: isUnknown ? "#ef4444" : "#10b981",
                        lineWidth: 2
                    });
                    drawBox.draw(canvasOverlay);
                });
            }
        } catch (err) {
            console.error("Error running scanning frame execution:", err);
        }
        
        requestAnimationFrame(runScanningLoop);
    }

    async function markAttendanceLocally(name) {
        const uppercaseName = name.trim().toUpperCase();
        const today = getTodayFormattedString();
        
        let attendance = JSON.parse(localStorage.getItem('attendance')) || [];
        
        // Unique attendance check: check if already logged today
        const alreadyLogged = attendance.some(log => log.Name === uppercaseName && log.Date === today);
        
        if (!alreadyLogged) {
            const now = new Date();
            const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
            
            // 1. Post to Python Flask backend
            let savedOnBackend = false;
            try {
                const response = await fetch(`${API_BASE}/api/mark_attendance`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: uppercaseName })
                });
                if (response.ok) {
                    savedOnBackend = true;
                }
            } catch (backendErr) {
                console.warn("Backend offline. Marking locally.", backendErr);
            }

            // 2. Sync client-side fallback
            attendance.push({
                Name: uppercaseName,
                Date: today,
                Time: timeStr
            });
            localStorage.setItem('attendance', JSON.stringify(attendance));
            
            // Update Timeline Logs
            loadTimelineLogs();
            
            // Pop dynamic Success Toast
            if (savedOnBackend) {
                showToast("Attendance Marked", `${uppercaseName} checked in. Saved inside attendance.csv!`);
            } else {
                showToast("Attendance Marked", `${uppercaseName} checked in (Local Storage Mode).`);
            }
        }
    }
}

function loadTimelineLogs() {
    const today = getTodayFormattedString();
    const attendance = JSON.parse(localStorage.getItem('attendance')) || [];
    
    // Filter attendance records to show only today's scans
    const todayLogs = attendance.filter(log => log.Date === today);
    
    const countBadge = document.getElementById('today-log-count');
    if (countBadge) {
        countBadge.textContent = `${todayLogs.length} Present`;
    }
    
    const container = document.getElementById('attendance-timeline');
    if (container) {
        container.innerHTML = '';
        
        if (todayLogs.length === 0) {
            container.innerHTML = '<div class="timeline-empty">Scanner is active. Stand in front to check in.</div>';
            return;
        }
        
        // Show newest check-ins first (newest on top)
        const reverseLogs = [...todayLogs].reverse();
        reverseLogs.forEach(row => {
            const item = document.createElement('div');
            item.className = 'timeline-item';
            item.innerHTML = `
                <div class="timeline-student-info">
                    <h4>${row.Name}</h4>
                    <span>Checked In Today</span>
                </div>
                <div class="timeline-time-badge">${row.Time}</div>
            `;
            container.appendChild(item);
        });
    }
}

function getTodayFormattedString() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    return `${day}-${month}-${year}`;
}

/* ==========================================================================
   TAB 4: ATTENDANCE RECORDS DATABASE FILTER ENGINE
   ========================================================================== */
function initRecordsDatabase() {
    const searchInput = document.getElementById('records-search');
    const dateInput = document.getElementById('records-date-filter');
    const btnClear = document.getElementById('btn-clear-filters');
    const btnRefresh = document.getElementById('btn-refresh-records');
    const btnDownload = document.getElementById('btn-download-csv');

    if (searchInput) searchInput.addEventListener('input', applyRecordsFilters);
    if (dateInput) dateInput.addEventListener('change', applyRecordsFilters);
    
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            searchInput.value = '';
            dateInput.value = '';
            applyRecordsFilters();
        });
    }

    if (btnRefresh) {
        btnRefresh.addEventListener('click', async () => {
            await syncWithBackend();
            loadFullAttendanceRecords();
        });
    }

    if (btnDownload) {
        btnDownload.addEventListener('click', () => {
            const students = JSON.parse(localStorage.getItem('students')) || [];
            const attendance = JSON.parse(localStorage.getItem('attendance')) || [];
            
            if (students.length === 0 && attendance.length === 0) {
                showToast("No Data", "There is no data to export.", "badge-red");
                return;
            }
            
            let csvContent = "";
            
            // 1. Registered Students Section
            csvContent += "=== REGISTERED STUDENTS DATABASE ===\n";
            csvContent += "Student Name,Email Address,Class/Semester,No. of Face Samples\n";
            students.forEach(row => {
                const line = [
                    row.name,
                    row.email,
                    row.class_name,
                    row.descriptors ? row.descriptors.length : 0
                ].map(val => `"${String(val).replace(/"/g, '""')}"`).join(",");
                csvContent += line + "\n";
            });
            
            csvContent += "\n"; // Blank separator line
            
            // 2. Attendance Logs Section
            csvContent += "=== ATTENDANCE LOGS DATABASE ===\n";
            csvContent += "Student Name,Date Logged,Time Registered\n";
            attendance.forEach(row => {
                const line = [
                    row.Name,
                    row.Date,
                    row.Time
                ].map(val => `"${String(val).replace(/"/g, '""')}"`).join(",");
                csvContent += line + "\n";
            });
            
            // Create Downloadable Blob URL
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            
            link.setAttribute("href", url);
            link.setAttribute("download", `attendance_and_students_report_${new Date().toISOString().slice(0, 10)}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showToast("CSV Exported", "Unified CSV report downloaded successfully.");
        });
    }
}

function loadFullAttendanceRecords() {
    const tbody = document.getElementById('table-records-body');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-records">Refreshing logs...</td></tr>';
    }
    
    // Read local storage database
    const attendance = JSON.parse(localStorage.getItem('attendance')) || [];
    globalRecords = attendance; // Cache
    applyRecordsFilters();
}

function applyRecordsFilters() {
    const tbody = document.getElementById('table-records-body');
    if (!tbody) return;
    
    const searchInput = document.getElementById('records-search');
    const dateInput = document.getElementById('records-date-filter');
    
    const searchQuery = searchInput ? searchInput.value.trim().toUpperCase() : '';
    const dateQuery = dateInput ? dateInput.value : ''; // Formats: YYYY-MM-DD
    
    // Parse date filter to DD-MM-YYYY matching local format
    let formattedDateQuery = '';
    if (dateQuery) {
        const parts = dateQuery.split('-');
        if (parts.length === 3) {
            formattedDateQuery = `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
    }

    tbody.innerHTML = '';

    // Filter condition matching
    const filtered = globalRecords.filter(row => {
        const matchName = !searchQuery || String(row.Name).toUpperCase().includes(searchQuery);
        const matchDate = !formattedDateQuery || String(row.Date) === formattedDateQuery;
        return matchName && matchDate;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="no-records">No matching records found.</td></tr>';
        return;
    }

    // Render table rows (newest first)
    const reversedFiltered = [...filtered].reverse();
    reversedFiltered.forEach(row => {
        const tr = document.createElement('tr');
        tr.className = 'animate-fade';
        tr.innerHTML = `
            <td style="font-weight:600; text-transform: uppercase;">${row.Name}</td>
            <td>${row.Date}</td>
            <td style="font-family: monospace; font-weight:500;">${row.Time}</td>
            <td><span class="badge badge-purple">FACIAL VERIFIED</span></td>
            <td>
                <button class="btn-delete" style="padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border-glass); background: transparent; color: var(--accent-red); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; transition: all 0.2s ease;" onclick="deleteAttendanceRecord('${row.Name.replace(/'/g, "\\'")}', '${row.Date}', '${row.Time}')" title="Delete Attendance Log">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function deleteAttendanceRecord(name, date, time) {
    if (confirm(`Are you sure you want to delete the attendance log for "${name}" on ${date} at ${time}?`)) {
        const uppercaseName = name.trim().toUpperCase();
        
        // 1. Try deleting from Flask backend
        try {
            const response = await fetch(`${API_BASE}/api/delete_attendance`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: uppercaseName, date: date, time: time })
            });
            if (response.ok) {
                console.log("Deleted attendance record from Python backend.");
            }
        } catch (err) {
            console.warn("Python backend offline. Deleting from local storage only.", err);
        }

        // 2. Delete from local storage fallback
        let attendance = JSON.parse(localStorage.getItem('attendance')) || [];
        attendance = attendance.filter(log => !(log.Name === uppercaseName && log.Date === date && log.Time === time));
        localStorage.setItem('attendance', JSON.stringify(attendance));

        // 3. Refresh UI views
        loadDashboardData();
        loadTimelineLogs();
        loadFullAttendanceRecords();
        showToast("Record Deleted", `Attendance log for ${uppercaseName} was deleted.`);
    }
}
window.deleteAttendanceRecord = deleteAttendanceRecord;

/* ==========================================================================
   THEME TOGGLE ENGINE (LIGHT / DARK MODE)
   ========================================================================== */
function initThemeToggle() {
    const themeBtn = document.getElementById('theme-toggle');
    if (!themeBtn) return;
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    // Retrieve saved user theme selection or default to dark
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'block';
    }

    themeBtn.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('light-theme');
        if (isLight) {
            localStorage.setItem('theme', 'light');
            if (sunIcon) sunIcon.style.display = 'none';
            if (moonIcon) moonIcon.style.display = 'block';
        } else {
            localStorage.setItem('theme', 'dark');
            if (sunIcon) sunIcon.style.display = 'block';
            if (moonIcon) moonIcon.style.display = 'none';
        }
    });
}

/* ==========================================================================
   WIDGET: PREMIUM SUCCESS TOAST NOTIFICATIONS
   ========================================================================== */
function showToast(title, message, badgeClass = 'badge-green') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast animate-fade';
    
    // Choose icon base color based on badge styling
    const iconColor = badgeClass === 'badge-red' ? 'hsl(var(--accent-red))' : 'hsl(var(--accent-green))';
    
    toast.innerHTML = `
        <div class="toast-icon" style="color: ${iconColor}">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
        </div>
        <div class="toast-content">
            <h4>${title}</h4>
            <p>${message}</p>
        </div>
        <button class="toast-close" aria-label="Close Toast">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Trigger reflow to run CSS cubic-bezier transition
    toast.offsetHeight;

    // Show slide-in toast
    toast.classList.add('show');

    // Bind click dismiss behavior
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => dismissToast(toast));

    // Auto-remove after 5 seconds
    setTimeout(() => {
        dismissToast(toast);
    }, 5000);
}

function dismissToast(toast) {
    if (!toast.parentNode) return;
    toast.classList.remove('show');
    toast.addEventListener('transitionend', () => {
        toast.remove();
    });
}
