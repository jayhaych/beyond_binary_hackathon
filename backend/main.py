import os
import shutil
import uuid
import json
import dotenv
import io
import wave
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pdf2image import convert_from_bytes
import easyocr
import numpy as np
from elevenlabs.client import ElevenLabs
import google.generativeai as genai
from vosk import Model, KaldiRecognizer
import json as json_lib

# IMPORT YOUR NEW QUIZ MODULE
import quiz  # Assumes filename is quiz.py

app = FastAPI()

# --- CONFIGURATION ---
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
dotenv.load_dotenv()

# Update this path for your Windows machine!
POPPLER_PATH = r'C:\poppler\poppler-25.12.0\Library\bin'

# Initialize Vosk Model (US English)
try:
    vosk_model = Model("model")
    print("✅ Vosk model loaded successfully")
except Exception as e:
    print(f"⚠️ Vosk model loading error: {e}")
    vosk_model = None

# Request model for transcription
class TranscribeRequest(BaseModel):
    audio_base64: str  # Base64 encoded WAV audio data

# Initialize Tools
reader = easyocr.Reader(['en'])

# Check for ElevenLabs API key
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
if not elevenlabs_key or elevenlabs_key.startswith("your_"):
    print("⚠️  WARNING: ELEVENLABS_API_KEY not set in .env file!")
    print("    PDF to Audio conversion will fail.")
    print("    Paste your API key into backend/.env: ELEVENLABS_API_KEY=your_key")
    client = None
else:
    client = ElevenLabs(api_key=elevenlabs_key)
    print("✅ ElevenLabs API key loaded")

# Gemini Setup
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key or gemini_key.startswith("your_"):
    print("⚠️  WARNING: GEMINI_API_KEY not set in .env file!")
    print("    Quiz generation will fail.")
    print("    Paste your API key into backend/.env: GEMINI_API_KEY=your_key")
    model = None
else:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini API key loaded")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Text Store (This holds your PDF text!)
latest_extracted_text = {}

@app.post("/api/process-notes")
async def process_notes(file: UploadFile = File(...)):
    # 1. Save PDF
    unique_id = str(uuid.uuid4())[:8]
    pdf_filename = f"{unique_id}_{file.filename}"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 2. Convert & OCR
    try:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()     
        pages = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
    except Exception as e:
        return {"error": f"Poppler failed: {str(e)}"}

    full_text = ""
    for page in pages:
        page_np = np.array(page)
        text_list = reader.readtext(page_np, detail=0, paragraph=True)
        full_text += " ".join(text_list) + " "

    # [CRITICAL] Save text to global memory
    latest_extracted_text["content"] = full_text
    print(f"✅ Extracted {len(full_text)} characters.")

    # 3. Generate Audio
    try:
        if not client:
            raise HTTPException(status_code=400, detail="ElevenLabs API key not configured. Add ELEVENLABS_API_KEY to backend/.env file")
        
        audio_generator = client.text_to_speech.convert(
            text=full_text[:500], 
            voice_id="pNInz6obpgDQGcFmaJgB",
            model_id="eleven_multilingual_v2"
        )
        audio_filename = f"{unique_id}_audio.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_filename)
        
        with open(audio_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
        
        return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_filename)

    except Exception as e:
        print(f"ElevenLabs Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate-quiz")
async def generate_quiz():
    text = latest_extracted_text.get("content", "")
    if not text:
        raise HTTPException(status_code=400, detail="No text found.")

    prompt = f"""
    Create a summary and a 5-question multiple choice quiz based on these notes.
    Output ONLY valid JSON:
    {{
        "summary": "Summary text",
        "quiz": [
            {{ "question": "Q?", "options": ["A","B","C","D"], "answer": "Option Text" }}
        ]
    }}
    NOTES: {text[:3000]}
    """
    try:
        if not model:
            raise Exception("Gemini API key not configured. Add GEMINI_API_KEY to backend/.env file")
        
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(clean_json))
    except Exception as e:
        return {"error": str(e)}

# --- [UPDATED] BLIND MODE ENDPOINT ---
# --- [UPDATED] BLIND MODE ENDPOINT ---
@app.post("/api/start-blind-quiz")
async def start_blind_quiz():
    """
    BLOCKING CALL: Waits for the quiz to finish, then returns the results.
    """
    text_content = latest_extracted_text.get("content", "")
    
    if not text_content:
        raise HTTPException(status_code=400, detail="No PDF text found! Upload a file first.")
    
    print("🚀 Starting Blind Mode Quiz...")
    
    # Run the quiz synchronously (waits until finished)
    # Note: For a hackathon this is fine. For production, you'd use WebSockets.
    results = quiz.run_quiz_from_text(text_content)
    
    if not results:
        raise HTTPException(status_code=500, detail="Quiz generation failed.")

    return JSONResponse(content=results)

@app.post("/api/transcribe-audio")
async def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe audio using Vosk
    Expects base64 encoded WAV audio data
    """
    if not vosk_model:
        print("❌ Vosk model not loaded!")
        raise HTTPException(status_code=500, detail="Vosk model not loaded")
    
    try:
        print(f"\n🎙️ === TRANSCRIPTION REQUEST ===")
        print(f"📥 Received audio data: {len(request.audio_base64)} chars (base64)")
        
        # Decode base64 audio
        import base64
        audio_bytes = base64.b64decode(request.audio_base64)
        print(f"📊 Decoded audio: {len(audio_bytes)} bytes")
        
        # Try to read as WAV
        audio_buffer = io.BytesIO(audio_bytes)
        try:
            with wave.open(audio_buffer, 'rb') as wav_file:
                # Get audio parameters
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                print(f"🎵 WAV Info: {n_channels} ch, {sample_width} bytes/sample, {sample_rate} Hz, {n_frames} frames")
                print(f"   Duration: {n_frames / sample_rate:.2f} seconds")
                
                # Create recognizer with detected sample rate
                recognizer = KaldiRecognizer(vosk_model, sample_rate)
                recognizer.SetWords([])  # Allow all words
                
                # Process audio in chunks
                transcript = ""
                chunk_count = 0
                
                while True:
                    # Read audio data in 4000-byte chunks
                    data = wav_file.readframes(4000)
                    if len(data) == 0:
                        break
                    
                    chunk_count += 1
                    result = recognizer.AcceptWaveform(data)
                    
                    if result:
                        # We got a partial result
                        partial_json = recognizer.Result()
                        print(f"  ✓ Chunk {chunk_count}: Got intermediate result")
                
                print(f"📝 Processed {chunk_count} chunks, requesting final result...")
                
                # Get final result
                final_json = recognizer.FinalResult()
                final_result = json_lib.loads(final_json)
                
                print(f"📋 Final result: {final_result}")
                
                # Extract transcript
                transcript = ""
                if "result" in final_result and isinstance(final_result["result"], list):
                    words = []
                    for item in final_result["result"]:
                        if isinstance(item, dict) and "word" in item:
                            word = item["word"]
                            print(f"   Word: '{word}' (conf: {item.get('conf', 0)})")
                            words.append(word)
                    transcript = " ".join(words)
                elif "text" in final_result:
                    # Handle direct text format from Vosk
                    transcript = final_result["text"]
                    print(f"   Text: '{transcript}'")
                elif "partial" in final_result:
                    transcript = final_result["partial"]
                    print(f"   Partial: '{transcript}'")
                
                transcript = transcript.strip()
                print(f"✅ Final transcript: '{transcript}'")
                
                return {
                    "transcript": transcript if transcript else "No speech detected",
                    "status": "success"
                }
        
        except wave.Error as e:
            print(f"⚠️ Not a valid WAV file: {e}, trying alternative processing...")
            raise
            
    except Exception as e:
        print(f"❌ Transcription error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)