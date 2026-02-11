import json
import os
import shutil
import subprocess
import uuid
import wave
from datetime import datetime
from pathlib import Path

import dotenv
import easyocr
import numpy as np
import google.generativeai as genai  # Added for Quiz
from elevenlabs.client import ElevenLabs
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pdf2image import convert_from_bytes
from vosk import KaldiRecognizer, Model

# IMPORT YOUR QUIZ MODULE
# Ensure you have a file named 'quiz.py' in the same directory
import quiz 

app = FastAPI()

# --- CONFIGURATION ---
# 1. Setup Folders
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
dotenv.load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BACKEND_DIR / "sample"
VOICE_UPLOADS_DIR = BACKEND_DIR / "voice_uploads"
MODELS_DIR = BACKEND_DIR / "models"
DEFAULT_VOSK_MODEL_DIR = MODELS_DIR / "vosk-model-small-en-us-0.15"

# 2. Setup Tools
# Update this path for your Windows machine!
POPPLER_PATH = r'C:\Release-24.08.0-0\poppler-24.08.0\Library\bin'

# Initialize AI Tools
reader = easyocr.Reader(['en'])

# ElevenLabs Setup
client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

# Gemini Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# --- GLOBAL STATE ---
# This dictionary holds the text from the most recently uploaded PDF
# so the quiz endpoints can access it.
latest_extracted_text = {} 

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- VOICE TO TEXT HELPERS (VOSK) ---

def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg and ensure `ffmpeg` is available."
        )

def _to_wav_16k_mono(input_path: Path, output_path: Path) -> None:
    """Convert arbitrary audio input to 16kHz mono WAV PCM (s16le) using ffmpeg."""
    _require_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed:\n{proc.stderr.strip()}")

def _load_vosk_model() -> Model:
    model_dir = Path(os.environ.get("VOSK_MODEL_DIR", str(DEFAULT_VOSK_MODEL_DIR)))
    if not model_dir.exists():
        raise RuntimeError(
            "Vosk model not found.\n"
            f"Expected at: {model_dir}\n"
            "Download a Vosk model and place it there, or set env var VOSK_MODEL_DIR."
        )
    return Model(str(model_dir))

def _transcribe_wav_with_vosk(wav_path: Path, model: Model) -> str:
    wf = wave.open(str(wav_path), "rb")
    try:
        if wf.getnchannels() != 1 or wf.getframerate() != 16000:
            raise RuntimeError("WAV must be 16kHz mono.")

        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        final = json.loads(rec.FinalResult())
        return (final.get("text") or "").strip()
    finally:
        wf.close()


# --- ENDPOINTS ---

@app.post("/api/process-notes")
async def process_notes(file: UploadFile = File(...)):
    """
    1. Saves PDF.
    2. OCRs text.
    3. Saves text to global memory (for quiz).
    4. Generates Audio (for study).
    """
    # --- STEP 1: SAVE THE PDF ---
    unique_id = str(uuid.uuid4())[:8]
    pdf_filename = f"{unique_id}_{file.filename}"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"✅ PDF saved to: {pdf_path}")

    # --- STEP 2: CONVERT TO IMAGES ---
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
    except Exception as e:
        return {"error": f"Poppler failed: {str(e)}"}

    # --- STEP 3: OCR EXTRACTION ---
    print(f"Processing {len(pages)} pages...")
    full_text = ""
    for i, page in enumerate(pages):
        page_np = np.array(page)
        text_list = reader.readtext(page_np, detail=0, paragraph=True)
        full_text += " ".join(text_list) + " "

    # [CRITICAL] Save text to global memory for the QUIZ endpoints
    latest_extracted_text["content"] = full_text
    print(f"✅ Extracted {len(full_text)} characters to memory.")

    # (Optional) Save the text transcript to disk
    txt_path = os.path.join(OUTPUT_DIR, f"{unique_id}_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    # --- STEP 4: GENERATE AUDIO ---
    print("Generating audio...")
    try:
        # Limit text to 500 chars to save ElevenLabs credits during testing
        audio_generator = client.text_to_speech.convert(
            text=full_text[:500], 
            voice_id="pNInz6obpgDQGcFmaJgB", # Adam
            model_id="eleven_multilingual_v2"
        )
        
        audio_filename = f"{unique_id}_audio.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_filename)
        
        with open(audio_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Audio saved to: {audio_path}")
        return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_filename)

    except Exception as e:
        print(f"ElevenLabs Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcribe-voice")
async def transcribe_voice(audio: UploadFile = File(...)):
    """
    Voice-to-text endpoint using Vosk.
    """
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    VOICE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    upload_id = uuid.uuid4().hex
    raw_path = VOICE_UPLOADS_DIR / f"{upload_id}--{audio.filename}"
    wav_path = VOICE_UPLOADS_DIR / f"{upload_id}.wav"

    try:
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        _to_wav_16k_mono(raw_path, wav_path)
        model = _load_vosk_model()
        text = _transcribe_wav_with_vosk(wav_path, model)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = f"transcript_{ts}.txt"
        out_path = SAMPLE_DIR / out_name
        out_path.write_text(text + ("\n" if text else ""), encoding="utf-8")

        return {"text": text, "saved_as": f"backend/sample/{out_name}"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files
        for p in [raw_path, wav_path]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass


@app.get("/api/generate-quiz")
async def generate_quiz():
    """
    Generates a generic quiz based on the last uploaded PDF using Gemini.
    """
    text = latest_extracted_text.get("content", "")
    if not text:
        raise HTTPException(status_code=400, detail="No text found. Upload a PDF first.")

    prompt = f"""
    Create a summary and a 5-question multiple choice quiz based on these notes.
    Output ONLY valid JSON in this format:
    {{
        "summary": "Summary text",
        "quiz": [
            {{ "question": "Q?", "options": ["A","B","C","D"], "answer": "Option Text" }}
        ]
    }}
    NOTES: {text[:3000]}
    """
    try:
        response = gemini_model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(clean_json))
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/start-blind-quiz")
async def start_blind_quiz():
    """
    Starts the 'Blind Mode' quiz using the imported 'quiz.py' module.
    """
    text_content = latest_extracted_text.get("content", "")
    
    if not text_content:
        raise HTTPException(status_code=400, detail="No PDF text found! Upload a file first.")
    
    print("🚀 Starting Blind Mode Quiz...")
    
    # Run the quiz logic from quiz.py
    try:
        results = quiz.run_quiz_from_text(text_content)
        if not results:
            raise HTTPException(status_code=500, detail="Quiz generation returned empty.")
        return JSONResponse(content=results)
    except Exception as e:
        print(f"Blind Quiz Error: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz module failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)