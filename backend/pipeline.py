import os
from pdf2image import convert_from_path
import easyocr
from elevenlabs.client import ElevenLabs
import dotenv
import numpy as np

# --- CONFIGURATION ---
# Update this path to where you extracted Poppler
POPPLER_PATH = r'C:\Release-24.08.0-0\poppler-24.08.0\Library\bin'
# Use a sample PDF in your folder
PDF_FILE = 'testing1.pdf' 

dotenv.load_dotenv()

# 1. Initialize Tools
print("Initializing OCR Reader...")
reader = easyocr.Reader(['en'])
client = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)


def run_test():
    if not os.path.exists(PDF_FILE):
        print(f"Error: {PDF_FILE} not found. Put a PDF in this folder!")
        return

    # 2. Convert PDF to Images
    print("Splitting PDF into pages...")
    try:
        pages = convert_from_path(PDF_FILE, poppler_path=POPPLER_PATH)
    except Exception as e:
        print(f"Poppler Error: {e}")
        return

    # 3. Run OCR
    print(f"Starting OCR on {len(pages)} pages...")
    full_text = ""
    for i, page in enumerate(pages):
            # Convert the PIL image to a numpy array so EasyOCR can read it
            page_np = np.array(page) 
            
            # Now pass the numpy array instead of 'page'
            text_list = reader.readtext(page_np, detail=0, paragraph=True)
            
            page_text = " ".join(text_list)
            full_text += f"\n[Page {i+1}]\n{page_text}\n"
            print(f"Page {i+1} complete.")

    # 4. Save Text Result
    with open("extracted_notes.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
    print("Text saved to extracted_notes.txt")

    
    # 5. Test ElevenLabs (First 200 chars only to save credits)
    print("Generating sample audio (first 200 chars)...")
    audio_stream = client.text_to_speech.convert(
        text=full_text[:200], 
        voice_id="pNInz6obpgDQGcFmaJgB", # Adam
        model_id="eleven_multilingual_v2"
    )

    # Save audio file
    with open("test_audio.mp3", "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)
    
    print("Audio saved to test_audio.mp3")
    print("Test Complete!")

    

if __name__ == "__main__":
    run_test()