import os
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import easyocr
from elevenlabs.client import ElevenLabs
import numpy as np
from pathlib import Path

app = Flask(__name__)

# --- CONFIGURATION ---
POPPLER_PATH = r'C:\Release-24.08.0-0\poppler-24.08.0\Library\bin'
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf'}

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize tools (do this once at startup)
print("Initializing OCR Reader...")
reader = easyocr.Reader(['en'])
client = ElevenLabs(api_key="3864a81c83172f7f9fc91f053a3496d19be9d5dab034f50b6b538208cc59b458")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    try:
        # Check if file was uploaded
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)
        
        # Get character limit from request (default to full text)
        char_limit = request.form.get('char_limit', type=int)
        
        # Process PDF
        print(f"Processing {filename}...")
        
        # Convert PDF to images
        print("Converting PDF to images...")
        pages = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        
        # Run OCR
        print(f"Running OCR on {len(pages)} pages...")
        full_text = ""
        for i, page in enumerate(pages):
            page_np = np.array(page)
            text_list = reader.readtext(page_np, detail=0, paragraph=True)
            page_text = " ".join(text_list)
            full_text += f"\n[Page {i+1}]\n{page_text}\n"
            print(f"Page {i+1} complete.")
        
        # Save extracted text
        base_name = Path(filename).stem
        text_filename = f"{base_name}_extracted.txt"
        text_path = os.path.join(app.config['OUTPUT_FOLDER'], text_filename)
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        # Generate audio
        print("Generating audio...")
        audio_text = full_text if char_limit is None else full_text[:char_limit]
        
        audio_stream = client.text_to_speech.convert(
            text=audio_text,
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam
            model_id="eleven_multilingual_v2"
        )
        
        # Save audio file
        audio_filename = f"{base_name}_audio.mp3"
        audio_path = os.path.join(app.config['OUTPUT_FOLDER'], audio_filename)
        
        with open(audio_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)
        
        # Clean up uploaded PDF
        os.remove(pdf_path)
        
        return jsonify({
            'success': True,
            'text_file': text_filename,
            'audio_file': audio_filename,
            'text_length': len(full_text),
            'audio_length': len(audio_text)
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_type>/<filename>')
def download_file(file_type, filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)