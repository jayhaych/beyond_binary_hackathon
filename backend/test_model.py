import cv2
import json
import numpy as np
import keras
from keras.applications.mobilenet_v2 import preprocess_input  # FIXED: Import preprocessing
from collections import deque
import time

print("="*60)
print("REAL-TIME GESTURE RECOGNITION TESTER")
print("="*60)

# Load model and classes
try:
    model = keras.models.load_model('gesture_model_improved.keras')
    print("✓ Loaded improved model")
except:
    try:
        model = keras.models.load_model('gesture_model.keras')
        print("✓ Loaded standard model")
    except Exception as e:
        print(f"ERROR: No model found! {e}")
        print("Train the model first using: python trainmodel_improved_FIXED.py")
        exit(1)

try:
    with open('classes.json', 'r') as f:
        class_map = json.load(f)
    print(f"✓ Loaded {len(class_map)} gesture classes")
    print(f"  Classes: {list(class_map.values())}")
except Exception as e:
    print(f"ERROR: Could not load classes.json: {e}")
    exit(1)

# Configuration
IMG_SIZE = 224
CONFIDENCE_THRESHOLD = 0.60  # Only show predictions above 60% confidence
SMOOTHING_WINDOW = 10  # Average predictions over last 10 frames

# Prediction smoothing
prediction_buffer = deque(maxlen=SMOOTHING_WINDOW)


def detect_skin(frame):
    """Enhanced skin detection"""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    
    lower_skin_hsv = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin_hsv = np.array([20, 255, 255], dtype=np.uint8)
    mask_hsv = cv2.inRange(hsv, lower_skin_hsv, upper_skin_hsv)
    
    lower_skin_ycrcb = np.array([0, 135, 85], dtype=np.uint8)
    upper_skin_ycrcb = np.array([255, 180, 135], dtype=np.uint8)
    mask_ycrcb = cv2.inRange(ycrcb, lower_skin_ycrcb, upper_skin_ycrcb)
    
    mask = cv2.bitwise_or(mask_hsv, mask_ycrcb)
    
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    return mask


def preprocess_frame(roi):
    """Preprocess frame for model prediction"""
    # Resize
    img = cv2.resize(roi, (IMG_SIZE, IMG_SIZE))
    # Convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # Preprocess for MobileNetV2 - FIXED: use imported function
    img = preprocess_input(img)
    # Add batch dimension
    img = np.expand_dims(img, axis=0)
    return img


def get_smoothed_prediction(current_probs):
    """Average predictions over time for stability"""
    prediction_buffer.append(current_probs)
    
    if len(prediction_buffer) < 3:
        return current_probs
    
    # Average the probabilities
    avg_probs = np.mean(prediction_buffer, axis=0)
    return avg_probs


def draw_hand_detection(frame, roi):
    """Draw hand detection overlay"""
    mask = detect_skin(roi)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    hand_count = 0
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        for contour in contours[:2]:
            area = cv2.contourArea(contour)
            if area > 3000:
                hand_count += 1
                cv2.drawContours(roi, [contour], -1, (0, 255, 0), 2)
                hull = cv2.convexHull(contour)
                cv2.drawContours(roi, [hull], -1, (0, 255, 255), 2)
    
    return hand_count > 0


def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("\n" + "="*60)
    print("CONTROLS:")
    print("  SPACE - Toggle prediction ON/OFF")
    print("  C - Clear prediction buffer")
    print("  Q - Quit")
    print("="*60 + "\n")
    
    predicting = True
    fps_start_time = time.time()
    fps_counter = 0
    fps = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Mirror frame
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # Define ROI
        roi_size = 500
        x1 = (w - roi_size) // 2
        y1 = (h - roi_size) // 2
        x2 = x1 + roi_size
        y2 = y1 + roi_size
        
        roi = frame[y1:y2, x1:x2].copy()
        
        # Detect hands
        hand_detected = draw_hand_detection(frame, frame[y1:y2, x1:x2])
        
        # Draw ROI box
        box_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
        
        # Prediction
        if predicting and hand_detected:
            try:
                # Preprocess
                processed = preprocess_frame(roi)
                
                # Predict
                predictions = model.predict(processed, verbose=0)[0]
                
                # Smooth predictions
                smooth_preds = get_smoothed_prediction(predictions)
                
                # Get top prediction
                top_idx = np.argmax(smooth_preds)
                top_conf = smooth_preds[top_idx]
                top_gesture = class_map[str(top_idx)]
                
                # Display prediction
                if top_conf >= CONFIDENCE_THRESHOLD:
                    # Main prediction
                    text = f"{top_gesture}"
                    conf_text = f"{top_conf*100:.1f}%"
                    
                    # Draw background for text
                    cv2.rectangle(frame, (10, 10), (600, 120), (0, 0, 0), -1)
                    
                    cv2.putText(frame, text, (20, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    cv2.putText(frame, conf_text, (20, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                    
                    # Show top 3 predictions
                    top_3_idx = np.argsort(smooth_preds)[-3:][::-1]
                    y_offset = 150
                    
                    cv2.putText(frame, "Top 3:", (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    y_offset += 30
                    
                    for idx in top_3_idx:
                        gesture = class_map[str(idx)]
                        conf = smooth_preds[idx]
                        text = f"{gesture}: {conf*100:.1f}%"
                        color = (0, 255, 0) if idx == top_idx else (200, 200, 200)
                        cv2.putText(frame, text, (10, y_offset),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        y_offset += 25
                else:
                    # Low confidence
                    cv2.putText(frame, "Low Confidence", (20, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 2)
                    cv2.putText(frame, f"Max: {top_conf*100:.1f}%", (20, 100),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            except Exception as e:
                cv2.putText(frame, f"Error: {str(e)[:30]}", (20, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Status info
        status = "PREDICTING" if predicting else "PAUSED"
        status_color = (0, 255, 0) if predicting else (0, 165, 255)
        cv2.putText(frame, status, (w - 200, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Hand detection status
        hand_status = "Hand Detected ✓" if hand_detected else "No Hand"
        hand_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        cv2.putText(frame, hand_status, (w - 250, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, hand_color, 2)
        
        # FPS
        fps_counter += 1
        if time.time() - fps_start_time >= 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_start_time = time.time()
        
        cv2.putText(frame, f"FPS: {fps}", (w - 150, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Controls
        cv2.putText(frame, "SPACE=Toggle | C=Clear | Q=Quit", (10, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('Gesture Recognition Test', frame)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord(' '):
            predicting = not predicting
            print(f"Prediction {'ON' if predicting else 'OFF'}")
        elif key == ord('c'):
            prediction_buffer.clear()
            print("Prediction buffer cleared")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Test complete!")


if __name__ == "__main__":
    main()