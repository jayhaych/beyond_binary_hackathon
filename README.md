# OmniLearn - Inclusive Learning Platform

An accessible, multi-modal learning platform designed for everyone. Convert PDFs to interactive audio lessons, generate voice-controlled quizzes, and transcribe speech to text - all with a beautiful, inclusive interface supporting visual, audio, and text-based learning.

## 🎯 Project Overview

**OmniLearn** is a hackathon project that combines modern AI technologies to create an inclusive learning experience:

- **PDF to Podcast**: Convert lecture notes to natural speech audio
- **AI-Powered Quizzes**: Generate intelligent quiz questions from extracted text
- **Voice-Controlled Learning**: Interactive voice quizzes for hands-free studying
- **Speech-to-Text**: Convert spoken words to text for transcription
- **Multi-Modal Interface**: Visual, audio, and text-based learning modes

## 🏗️ Architecture

```
Beyond_Binary_Hackathon/
├── frontend/                  # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx           # Main application component
│   │   ├── main.jsx          # React entry point
│   │   └── index.css         # Global styles
│   ├── package.json          # Frontend dependencies
│   ├── vite.config.js        # Vite configuration
│   └── tailwind.config.js    # Tailwind CSS configuration
│
├── backend/                   # FastAPI + Python
│   ├── main.py               # FastAPI server & API endpoints
│   ├── quiz.py               # Voice quiz logic
│   ├── pipeline.py           # PDF processing pipeline
│   ├── TTS.py                # Text-to-speech test utility
│   ├── requirement.txt       # Python dependencies
│   ├── .env                  # Environment variables (API keys)
│   └── model/                # Vosk speech recognition model
│       ├── am/               # Acoustic model
│       ├── conf/             # Configuration files
│       ├── graph/            # Language graph
│       └── ivector/          # iVector model
│
└── README.md                 # This file
```

## ✨ Features

### 1. **Visual Learning Mode**

- Upload PDF files
- Automatic text extraction using OCR
- Convert text to natural speech audio
- Generate interactive quizzes with multiple-choice questions
- View quiz summaries and test knowledge

### 2. **Audio Learning Mode (Blind Mode)**

- Voice-controlled quiz experience
- AI reads questions and options aloud
- Record verbal answers to quiz questions
- Real-time feedback on answers
- Accessible interface for visually impaired users

### 3. **Transcription Mode**

- Record audio from microphone
- Convert speech to text using Vosk speech recognition
- Copy transcripts to clipboard
- View recording playback

### 4. **Sign Language Mode**

- Coming soon - placeholder for future accessibility feature

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Poppler** (for PDF processing)
- **Microphone** (for speech features)

### Backend Setup

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirement.txt
   ```

3. **Configure API keys:**
   Create a `.env` file in the `backend/` directory:

   ```env
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

4. **Install Poppler** (Windows):
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to `C:\poppler\` (or update `POPPLER_PATH` in `main.py`)

5. **Start the backend server:**
   ```bash
   python main.py
   ```
   The server will run at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**

   ```bash
   cd frontend
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

### Running Both Services

**Terminal 1 - Backend:**

```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

## 📡 API Endpoints

All endpoints are hosted at `http://localhost:8000`

### POST `/api/process-notes`

**Upload and process a PDF file**

- **Request:** Multipart form data with PDF file
- **Response:** Audio file (MP3) of extracted text converted to speech
- **Uses:**
  - `pdf2image` - Convert PDF pages to images
  - `easyocr` - Extract text from images
  - `ElevenLabs API` - Convert text to natural speech audio

**Frontend Function:** `handleFileUpload(file)`

---

### GET `/api/generate-quiz`

**Generate quiz from the last uploaded PDF**

- **Request:** None (uses stored PDF text from previous upload)
- **Response:** JSON with summary and quiz questions
  ```json
  {
    "summary": "Summary of lecture notes",
    "quiz": [
      {
        "question": "What is...?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A"
      }
    ]
  }
  ```
- **Uses:** `Google Gemini API` - Generate quiz questions intelligently

**Frontend Function:** `handleGenerateQuiz()`

---

### POST `/api/start-blind-quiz`

**Initiate voice-controlled quiz session**

- **Request:** None (uses stored PDF text)
- **Response:** Quiz results with score and answers
  ```json
  {
    "score": 2,
    "total": 3,
    "questions": [
      {
        "q": "Question text",
        "options": ["A", "B", "C", "D"],
        "correct": "A"
      }
    ]
  }
  ```
- **Uses:**
  - `Google Gemini API` - Generate questions
  - `pyttsx3` - Text-to-speech for reading questions
  - `SpeechRecognition` - Recognize user's spoken answers
  - `Vosk` - Offline speech recognition model

**Frontend Function:** `handleStartBlindMode()`

---

### POST `/api/transcribe-audio`

**Transcribe audio to text**

- **Request:**
  ```json
  {
    "audio_base64": "base64_encoded_audio_data"
  }
  ```
- **Response:**
  ```json
  {
    "transcript": "Transcribed text",
    "status": "success"
  }
  ```
- **Uses:** `Vosk` - Offline speech recognition

**Frontend Functions:** `startRecording()`, `stopRecording()`, `arrayBufferToBase64()`

## 🔧 Backend Functions & Modules

### main.py - FastAPI Server

**Key Functions:**

1. **`process_notes(file: UploadFile)`**
   - Saves PDF file
   - Converts PDF to images
   - Runs OCR to extract text
   - Converts text to speech using ElevenLabs
   - Stores text in global memory for quiz generation
   - Returns audio file response

2. **`generate_quiz()`**
   - Retrieves stored PDF text
   - Prompts Gemini AI to create quiz questions
   - Parses JSON response
   - Returns quiz data

3. **`start_blind_quiz()`**
   - Calls `quiz.run_quiz_from_text()`
   - Waits for voice quiz to complete
   - Returns quiz results

4. **`transcribe_audio(request: TranscribeRequest)`**
   - Decodes base64 audio
   - Reads WAV audio properties
   - Processes audio chunks with Vosk recognizer
   - Returns transcribed text

### quiz.py - Voice Quiz Module

**Key Classes & Functions:**

1. **`speak(text: str)`**
   - Uses `pyttsx3` to convert text to speech
   - Reads question and options aloud
   - Provides feedback on answers

2. **`listen_for_answer() -> str | None`**
   - Captures audio from microphone
   - Uses Google Speech Recognition API
   - Fuzzy matches response to A/B/C/D options
   - Handles multiple pronunciation variations

3. **`VoiceQuiz` Class:**
   - **`__init__(gemini_api_key)`** - Initialize with Gemini API
   - **`generate(text_content)`** - Generate quiz questions from text using Gemini
   - **`start_interactive_session(text_content)`** - Run full voice quiz loop:
     - Generate questions
     - Read questions and options aloud
     - Listen for user answers
     - Score responses
     - Return results

4. **`run_quiz_from_text(text: str)`**
   - Wrapper function called by main.py
   - Creates VoiceQuiz instance
   - Returns quiz results

### pipeline.py - PDF Processing Test

Test/utility script for the PDF processing pipeline:

- Load PDF file
- Extract text via OCR
- Save text to file
- Generate sample audio

## 🎨 Frontend Components & Functions

**React App.jsx - Main Application**

### State Management

```javascript
// Page & UI
showLanding; // Landing page display
currentPage; // Current page (text-to-audio, blind-mode, audio-to-text, sign-language)
sidebarOpen; // Sidebar visibility

// Text-to-Audio
status; // Upload status (idle, uploading, processing, success, error)
audioUrl; // Generated audio URL
quizData; // Quiz questions and summary
showQuiz; // Quiz display toggle
errorMessage; // Error feedback
duplicateFileName; // Duplicate file warning

// Audio Learning (Blind Mode)
blindModeStatus; // Quiz session status
blindQuizResults; // Quiz results

// Transcription
isRecording; // Recording state
transcriptText; // Transcribed text
transcriptStatus; // Transcription status
recordingTime; // Recording duration
lastRecordingUrl; // Last recording playback URL

// History
uploadHistory; // Array of uploaded files
```

### Key Functions

1. **`speakUI(text: string)`**
   - Uses Web Speech API for browser-based TTS
   - Spoken welcome message on landing page
   - Clears previous speech before speaking

2. **`handleFileUpload(file: File)`**
   - Validates PDF file
   - Checks for duplicates
   - Sends to `/api/process-notes`
   - Stores in upload history
   - Auto-plays generated audio

3. **`handleGenerateQuiz()`**
   - Calls `/api/generate-quiz`
   - Stores quiz data in state
   - Displays quiz interface

4. **`handleStartBlindMode()`**
   - Calls `/api/start-blind-quiz`
   - Speaks confirmation message
   - Displays quiz results

5. **Recording Functions:**
   - **`startRecording()`** - Initialize microphone and MediaRecorder
   - **`stopRecording()`** - Stop recording and process audio
   - **`audioBufferToWav(audioBuffer)`** - Convert WebAudioAPI buffer to WAV
   - **`encodeWAV(samples, sampleRate)`** - Encode PCM samples to WAV format
   - **`arrayBufferToBase64(buffer)`** - Safe base64 encoding for large data

6. **UI Navigation:**
   - **`enterVisualMode()`** - Switch to Visual Learning
   - **`enterAudioMode()`** - Switch to Audio Learning (Blind Mode)
   - **`goHome()`** - Return to landing page

## ⚙️ Configuration

### Environment Variables (.env)

```env
# ElevenLabs API Key
# Sign up at: https://elevenlabs.io/
# This enables Text-to-Speech audio generation
ELEVENLABS_API_KEY=sk_...

# Google Gemini API Key
# Get from: https://aistudio.google.com/app/apikey
# This enables AI quiz generation
GEMINI_API_KEY=AIza...
```

### Backend Configuration

**main.py:**

- `UPLOAD_DIR` = "uploads" - Directory for uploaded PDFs
- `OUTPUT_DIR` = "outputs" - Directory for generated audio files
- `POPPLER_PATH` = Poppler binary location (Windows path)

**Quiz Settings:**

- Vosk Model: "model/" - Offline speech recognition
- Recognized languages: English
- Microphone device index: 1 (configurable in quiz.py)
- Audio sensitivity threshold: 300

## 🎯 How It Works

### PDF to Podcast Flow

1. User uploads PDF → `/api/process-notes`
2. Backend extracts pages with pdf2image
3. EasyOCR reads text from each page
4. Text is sent to ElevenLabs API
5. Natural speech audio is generated and returned
6. Audio autoplay in frontend

### Quiz Generation Flow

1. User clicks "Generate Quiz & Summary"
2. Store PDF text is sent to Gemini API
3. Gemini generates 5 quiz questions
4. Summary is extracted
5. Frontend displays interactive quiz interface

### Voice Quiz Flow

1. User clicks "Start Voice Quiz" in Blind Mode
2. Backend calls `quiz.run_quiz_from_text()`
3. Questions are generated by Gemini
4. pyttsx3 speaks each question
5. SpeechRecognition listens for answer
6. Answer is evaluated
7. Feedback is spoken
8. Results returned and displayed

### Transcription Flow

1. User clicks "Start recording"
2. Browser requests microphone permission
3. Audio recorded using MediaRecorder API
4. Audio converted to WAV format
5. WAV encoded to base64
6. Sent to `/api/transcribe-audio`
7. Vosk processes audio chunks
8. Transcript returned and displayed

## 🐛 Troubleshooting

### "ELEVENLABS_API_KEY not set"

- Add API key to `.env` file
- Get key from https://elevenlabs.io/

### "GEMINI_API_KEY not set"

- Add Google API key to `.env`
- Get from https://aistudio.google.com/app/apikey

### "Poppler Error" (Windows)

- Ensure Poppler is installed
- Check POPPLER_PATH in main.py
- Download: https://github.com/oschwartz10612/poppler-windows/releases/

### "Vosk model not loaded"

- Ensure `model/` directory exists in backend/
- Contains: am/, conf/, graph/, ivector/ subdirectories

### "Microphone not detected"

- Check device_index in quiz.py (currently 1)
- Run `python -m speech_recognition` to list devices
- Update device_index accordingly

### "Recording Permission Denied"

- Browser is blocking microphone access
- Check HTTPS/localhost permissions
- Allow microphone access when prompted

### Frontend won't connect to backend

- Ensure backend is running on `http://localhost:8000`
- Check CORS is enabled (allowed in main.py)
- Verify no firewall blocks port 8000

## 📦 Dependencies

### Backend (Python)

- **FastAPI** - Web framework
- **pdf2image** - PDF to image conversion
- **easyocr** - Optical character recognition
- **elevenlabs** - Text-to-speech service
- **google-generativeai** - Gemini AI API
- **vosk** - Offline speech recognition
- **pyttsx3** - Text-to-speech engine
- **SpeechRecognition** - Speech recognition library
- **pydantic** - Data validation
- **python-dotenv** - Environment variable management

### Frontend (JavaScript/React)

- **React 19** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling framework
- **Heroicons** - Icon library
- **Web APIs** - MediaRecorder, AudioContext, SpeechSynthesis

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [ElevenLabs API](https://elevenlabs.io/docs)
- [Google Gemini API](https://ai.google.dev/)
- [Vosk Speech Recognition](https://alphacephei.com/vosk/)

## 👥 Team & Credits

### Team Members

- Tee Jia Hong
- Chu Shun Yuan
- Mao Ze Ming
- Nicole Wong Jing Han

### Technologies Used

- FastAPI (Python backend framework)
- React (Frontend library)
- Vite (Frontend build tool)
- Tailwind CSS (Design system)
- ElevenLabs (Text-to-speech)
- Google Gemini (AI assistant)
- Vosk (Speech recognition)

## 📄 License

This project is part of Beyond Binary Hackathon 2026.

---

**Last Updated:** February 11, 2026
**Version:** 1.0
