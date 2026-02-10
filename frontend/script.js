// API endpoint - adjust this to match your backend server
const API_BASE_URL = 'http://localhost:3000/api';

// Check if browser supports Web Speech API
if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Your browser does not support speech recognition. Please use Chrome or Edge.');
}

// Initialize Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

// DOM elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.getElementById('status');
const transcriptDiv = document.getElementById('transcript');
const fileContentDiv = document.getElementById('fileContent');
const errorDiv = document.getElementById('error');

// State
let isListening = false;
let currentUtterance = null;

// Event listeners
startBtn.addEventListener('click', startListening);
stopBtn.addEventListener('click', stopListening);

// Speech recognition event handlers
recognition.onstart = () => {
    isListening = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    status.textContent = '🎤 Listening... Speak the filename';
    status.className = 'status listening pulse';
    errorDiv.classList.remove('show');
    fileContentDiv.classList.remove('show');
};

recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    console.log('Transcript:', transcript);
    
    status.textContent = '⏳ Processing...';
    status.className = 'status processing';
    
    // Display transcript
    transcriptDiv.innerHTML = `
        <h3>You said:</h3>
        <p>"${transcript}"</p>
    `;
    
    // Extract filename from transcript
    const filename = extractFilename(transcript);
    
    // Fetch file from backend
    fetchFile(filename);
};

recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    isListening = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    let errorMessage = 'An error occurred with speech recognition.';
    if (event.error === 'no-speech') {
        errorMessage = 'No speech detected. Please try again.';
    } else if (event.error === 'audio-capture') {
        errorMessage = 'No microphone found. Please check your microphone.';
    } else if (event.error === 'not-allowed') {
        errorMessage = 'Microphone permission denied. Please allow microphone access.';
    }
    
    status.textContent = '';
    status.className = 'status';
    showError(errorMessage);
};

recognition.onend = () => {
    isListening = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (status.textContent === '🎤 Listening... Speak the filename') {
        status.textContent = '';
        status.className = 'status';
    }
};

// Extract filename from transcript (supports .txt and .pdf)
function extractFilename(transcript) {
    // Remove common phrases and extract filename
    let filename = transcript.toLowerCase();

    // Remove common prefixes
    filename = filename.replace(/^(read|open|get|show|display|load|find)\s+/i, '');

    // Remove common suffixes (but keep "pdf" for extension)
    filename = filename.replace(/\s+(file|text|document)$/i, '');

    // If user said "something pdf" or "something .pdf", use .pdf extension
    if (filename.endsWith(' pdf') || filename.endsWith(' .pdf')) {
        filename = filename.replace(/\s*\.?pdf\s*$/i, '.pdf');
    }

    // Remove quotes if present
    filename = filename.replace(/['"]/g, '');

    // Ensure extension if none: default to .txt unless we already have .pdf
    if (!filename.includes('.')) {
        filename = filename.trim() + '.txt';
    }

    filename = filename.trim();
    return filename;
}

// Fetch file from backend API
async function fetchFile(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/read-file?filename=${encodeURIComponent(filename)}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to read file');
        }
        
        // Display file content
        fileContentDiv.innerHTML = `
            <h3>File: ${filename}</h3>
            <pre>${data.content}</pre>
            <div class="audio-controls">
                <button id="speakBtn" class="speak-btn">🔊 Read Aloud</button>
                <button id="stopSpeakBtn" class="speak-btn" style="display: none;">⏹️ Stop</button>
            </div>
        `;
        fileContentDiv.classList.add('show');
        errorDiv.classList.remove('show');
        
        status.textContent = '✅ File read successfully!';
        status.className = 'status';
        
        // Set up audio controls
        const speakBtn = document.getElementById('speakBtn');
        const stopSpeakBtn = document.getElementById('stopSpeakBtn');
        
        speakBtn.addEventListener('click', () => speakText(data.content, filename));
        stopSpeakBtn.addEventListener('click', stopSpeaking);
        
        // Automatically start reading aloud
        speakText(data.content, filename);
        
    } catch (error) {
        console.error('Error fetching file:', error);
        showError(`File not found: "${filename}"`);
        status.textContent = '';
        status.className = 'status';
    }
}

// Show error message
function showError(message) {
    errorDiv.innerHTML = `
        <h3>❌ Error</h3>
        <p>${message}</p>
    `;
    errorDiv.classList.add('show');
    fileContentDiv.classList.remove('show');
}

// Start listening
function startListening() {
    try {
        recognition.start();
    } catch (error) {
        console.error('Error starting recognition:', error);
        showError('Could not start voice recognition. Please try again.');
    }
}

// Stop listening
function stopListening() {
    if (isListening) {
        recognition.stop();
    }
    // Also stop any ongoing speech
    stopSpeaking();
}

// Speak text using Web Speech Synthesis API
function speakText(text, filename) {
    // Stop any current speech
    stopSpeaking();
    
    // Create new utterance
    const utterance = new SpeechSynthesisUtterance();
    utterance.text = `Reading file ${filename}. ${text}`;
    utterance.lang = 'en-US';
    utterance.rate = 1.0; // Normal speed
    utterance.pitch = 1.0; // Normal pitch
    utterance.volume = 1.0; // Full volume
    
    // Update UI when speaking starts
    utterance.onstart = () => {
        status.textContent = '🔊 Reading aloud...';
        status.className = 'status processing';
        const speakBtn = document.getElementById('speakBtn');
        const stopSpeakBtn = document.getElementById('stopSpeakBtn');
        if (speakBtn) speakBtn.style.display = 'none';
        if (stopSpeakBtn) stopSpeakBtn.style.display = 'inline-block';
    };
    
    // Update UI when speaking ends
    utterance.onend = () => {
        status.textContent = '✅ File read successfully!';
        status.className = 'status';
        const speakBtn = document.getElementById('speakBtn');
        const stopSpeakBtn = document.getElementById('stopSpeakBtn');
        if (speakBtn) speakBtn.style.display = 'inline-block';
        if (stopSpeakBtn) stopSpeakBtn.style.display = 'none';
        currentUtterance = null;
    };
    
    // Handle errors
    utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        status.textContent = '⚠️ Error reading aloud';
        status.className = 'status';
        const speakBtn = document.getElementById('speakBtn');
        const stopSpeakBtn = document.getElementById('stopSpeakBtn');
        if (speakBtn) speakBtn.style.display = 'inline-block';
        if (stopSpeakBtn) stopSpeakBtn.style.display = 'none';
        currentUtterance = null;
    };
    
    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
}

// Stop speaking
function stopSpeaking() {
    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
    }
    currentUtterance = null;
    const speakBtn = document.getElementById('speakBtn');
    const stopSpeakBtn = document.getElementById('stopSpeakBtn');
    if (speakBtn) speakBtn.style.display = 'inline-block';
    if (stopSpeakBtn) stopSpeakBtn.style.display = 'none';
    if (status.textContent === '🔊 Reading aloud...') {
        status.textContent = '✅ File read successfully!';
        status.className = 'status';
    }
}
