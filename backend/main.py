import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
import easyocr
import numpy as np
from elevenlabs.client import ElevenLabs
import dotenv

app = FastAPI()

# --- CONFIGURATION ---
# 1. Setup Folders
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
dotenv.load_dotenv()

# 2. Setup Tools
# Update this path for your Windows machine!
POPPLER_PATH = r'C:\Release-24.08.0-0\poppler-24.08.0\Library\bin'

# Initialize AI Tools
reader = easyocr.Reader(['en'])
# RESTORE YOUR KEY SECURELY HERE (or use os.getenv)
client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)


# --- CORS (Connects to React) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process-notes")
async def process_notes(file: UploadFile = File(...)):
    # --- STEP 1: SAVE THE PDF ---
    # Create a unique filename so files don't overwrite each other
    unique_id = str(uuid.uuid4())[:8]
    pdf_filename = f"{unique_id}_{file.filename}"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)
    
    # Save the uploaded bytes to disk
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"✅ PDF saved to: {pdf_path}")

    # --- STEP 2: CONVERT TO IMAGES ---
    try:
        # We read the file we just saved
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
        # detail=0 + paragraph=True helps group text naturally
        text_list = reader.readtext(page_np, detail=0, paragraph=True)
        full_text += " ".join(text_list) + " "

    # (Optional) Save the text transcript too
    txt_path = os.path.join(OUTPUT_DIR, f"{unique_id}_transcript.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    # --- STEP 4: GENERATE AUDIO ---
    print("Generating audio...")
    try:
        audio_generator = client.text_to_speech.convert(
            text=full_text[:200], 
            voice_id="pNInz6obpgDQGcFmaJgB", # Adam
            model_id="eleven_multilingual_v2"
        )
        
        # --- STEP 5: SAVE AUDIO FILE ---
        audio_filename = f"{unique_id}_audio.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_filename)
        
        with open(audio_path, "wb") as f:
            for chunk in audio_generator:
                if chunk:
                    f.write(chunk)
        
        print(f"✅ Audio saved to: {audio_path}")

        # Return the audio file directly to the frontend to play
        return FileResponse(audio_path, media_type="audio/mpeg", filename=audio_filename)

    except Exception as e:
        print(f"ElevenLabs Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)