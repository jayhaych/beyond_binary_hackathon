import os
import json
import base64
import numpy as np
import cv2
import tensorflow as tf
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

app = Flask(__name__)
CORS(app)

print("="*60)
print("LOADING GESTURE MODEL")
print("="*60)

# 1. Matches the modern .keras format
MODEL_PATH = 'gesture_model.keras'
CLASSES_PATH = 'classes.json'

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model '{MODEL_PATH}' not found!")
    exit(1)

try:
    model = load_model(MODEL_PATH)
    print(f"✓ Model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"ERROR loading model: {e}")
    exit(1)

try:
    with open(CLASSES_PATH, 'r') as f:
        class_map = json.load(f)
    print(f"✓ Classes loaded: {list(class_map.values())}")
except Exception as e:
    print(f"ERROR loading classes: {e}")
    exit(1)

IMG_SIZE = 224

# 2. REQUIRED: Serves the HTML page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'No image'})
        
        # Decode image
        img_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(img_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess
        img_resized = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        
        # 3. CRITICAL: Matches MobileNetV2 training ([-1, 1] range)
        # Do NOT use / 255.0 here if you used preprocess_input in training
        img_norm = preprocess_input(img_rgb.astype('float32'))
        
        img_batch = np.expand_dims(img_norm, axis=0)
        
        # Predict
        predictions = model.predict(img_batch, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        gesture = class_map[str(class_idx)]
        
        return jsonify({
            'success': True,
            'gesture': gesture,
            'confidence': confidence
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)