import os
import shutil
import uuid
import json
import dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import easyocr
import numpy as np
from elevenlabs.client import ElevenLabs
import google.generativeai as genai

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

# Initialize Tools
reader = easyocr.Reader(['en'])
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Gemini Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

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
        response = model.generate_content(prompt)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(clean_json))
    except Exception as e:
        return {"error": str(e)}

# --- [UPDATED] BLIND MODE ENDPOINT ---
@app.post("/api/start-blind-quiz")
async def start_blind_quiz(background_tasks: BackgroundTasks):
    """
    1. Checks if text exists in memory.
    2. Starts the Voice Quiz in a BACKGROUND TASK.
    """
    # 1. Get the text
    text_content = latest_extracted_text.get("content", "")
    
    if not text_content:
        raise HTTPException(status_code=400, detail="No PDF text found! Upload a file first.")
    
    print("🚀 Starting Blind Mode Quiz with Real Text...")
    
    # 2. Run in background (So frontend doesn't freeze)
    background_tasks.add_task(quiz.run_quiz_from_text, text_content)
    
    return {"status": "Quiz Started on Server Speakers"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)