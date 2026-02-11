import cv2
import os
import time
import numpy as np


# 10 static gestures
GESTURES = [
    'HELLO',
    'I',
    'LIKE',
    'YOUR',
    'PERSPECTIVE',
    'THREE',
    'TIMES',
    'TWO',
    'EQUALS',
    'SIX'
]


BASE_DIR = 'dataset_static'
SAMPLES_PER_GESTURE = 300  # INCREASED from 200 for better training


# Create directories
for gesture in GESTURES:
    os.makedirs(f'{BASE_DIR}/{gesture}', exist_ok=True)


def detect_skin(frame):
    """Enhanced skin detection using multiple color spaces"""
    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Convert to YCrCb (better for skin detection)
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    
    # HSV skin range (handles different lighting better)
    lower_skin_hsv = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin_hsv = np.array([20, 255, 255], dtype=np.uint8)
    mask_hsv = cv2.inRange(hsv, lower_skin_hsv, upper_skin_hsv)
    
    # YCrCb skin range (more robust)
    lower_skin_ycrcb = np.array([0, 135, 85], dtype=np.uint8)
    upper_skin_ycrcb = np.array([255, 180, 135], dtype=np.uint8)
    mask_ycrcb = cv2.inRange(ycrcb, lower_skin_ycrcb, upper_skin_ycrcb)
    
    # Combine masks
    mask = cv2.bitwise_or(mask_hsv, mask_ycrcb)
    
    # Clean up mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.GaussianBlur(mask, (5,5), 0)
    
    return mask


def draw_hand_contours(frame, roi):
    """Draw contours around detected hand(s) - works for 1 or 2 hands"""
    mask = detect_skin(roi)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    hand_count = 0
    total_area = 0
    
    if contours:
        # Sort contours by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Process up to 2 largest contours (for 2 hands)
        for contour in contours[:2]:
            area = cv2.contourArea(contour)
            
            # Only draw if contour is big enough (filters out noise)
            if area > 3000:  # Lowered threshold to detect hands at various distances
                hand_count += 1
                total_area += area
                
                # Draw green contour around hand
                cv2.drawContours(roi, [contour], -1, (0, 255, 0), 2)
                
                # Draw convex hull (outline of hand)
                hull = cv2.convexHull(contour)
                cv2.drawContours(roi, [hull], -1, (0, 255, 255), 2)
                
                # Find center of hand
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(roi, (cx, cy), 8, (255, 0, 255), -1)
    
    hand_detected = hand_count > 0
    return hand_detected, hand_count, total_area


def add_noise_augmentation(roi):
    """Add random augmentation to make model more robust"""
    # Randomly apply one of these augmentations
    aug_choice = np.random.randint(0, 5)
    
    if aug_choice == 0:
        # Add Gaussian noise
        noise = np.random.normal(0, 5, roi.shape).astype(np.uint8)
        roi = cv2.add(roi, noise)
    elif aug_choice == 1:
        # Adjust brightness
        beta = np.random.randint(-30, 30)
        roi = cv2.convertScaleAbs(roi, alpha=1.0, beta=beta)
    elif aug_choice == 2:
        # Adjust contrast
        alpha = np.random.uniform(0.8, 1.2)
        roi = cv2.convertScaleAbs(roi, alpha=alpha, beta=0)
    elif aug_choice == 3:
        # Add blur
        roi = cv2.GaussianBlur(roi, (3, 3), 0)
    # else: no augmentation (original image)
    
    return roi


def collect_gesture(gesture_name, num_samples=300):
    """Collect images for one static gesture with flexible hand detection (1 or 2 hands)"""
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        return 0
    
    # Increase camera resolution for better quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # Increase FPS if possible
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    count = 0
    capturing = False
    
    print(f"\n{'='*60}")
    print(f"  Collecting: {gesture_name}")
    print(f"{'='*60}")
    print("  IMPROVED TIPS FOR HIGH ACCURACY:")
    print("  • LIGHTING: Use bright, even lighting (avoid shadows)")
    print("  • VARIETY: Rotate hand, tilt, move closer/farther")
    print("  • ANGLES: Try from different perspectives")
    print("  • HANDS: Use 1 or 2 hands as needed for gesture")
    print("  • BACKGROUND: Keep it simple and consistent")
    print("  • DISTANCE: Vary from close (fills box) to far (smaller)")
    print("  • SPEED: Move SLOWLY during capture")
    print("  • GREEN OUTLINE = Hand(s) detected!")
    print("")
    print("  1. Position your hand(s) in the GREEN box")
    print("  2. Wait for GREEN OUTLINE around your hand(s)")
    print("  3. Press SPACE to start auto-capture")
    print("  4. SLOWLY move hand(s) around for variety")
    print("  5. Press Q to quit early")
    print(f"{'='*60}\n")
    
    while count < num_samples:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Cannot read frame!")
            break
        
        # Mirror the frame
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        # LARGER ROI for better capture
        roi_size = 500  # Increased from 450
        x1 = (w - roi_size) // 2
        y1 = (h - roi_size) // 2
        x2 = x1 + roi_size
        y2 = y1 + roi_size
        
        # Extract ROI
        roi = frame[y1:y2, x1:x2].copy()
        
        # Detect and draw hand contours
        hand_detected, hand_count, total_area = draw_hand_contours(frame, frame[y1:y2, x1:x2])
        
        # Draw rectangle - GREEN if hand detected, RED if not
        if hand_detected:
            color = (0, 255, 0) if capturing else (0, 255, 255)
            if hand_count == 1:
                status_text = f"1 HAND DETECTED ✓ (area: {total_area})"
            else:
                status_text = f"{hand_count} HANDS DETECTED ✓ (area: {total_area})"
        else:
            color = (0, 0, 255)
            status_text = "NO HAND - Position hand(s) in box"
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
        
        # Display info
        if capturing:
            status = f"CAPTURING: {count}/{num_samples}"
        else:
            status = "READY (Press SPACE)" if hand_detected else "WAITING FOR HAND(S)..."
        
        cv2.putText(frame, gesture_name, (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
        cv2.putText(frame, status, (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, status_text, (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Progress bar
        progress = int((count / num_samples) * 100)
        cv2.putText(frame, f"Progress: {progress}%", (10, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw progress bar
        bar_width = 400
        bar_height = 20
        bar_x = 10
        bar_y = 200
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress / 100), bar_y + bar_height), (0, 255, 0), -1)
        
        # Instruction
        if capturing and hand_detected:
            cv2.putText(frame, "SLOWLY rotate & move hand(s)!", (10, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        cv2.putText(frame, "Q = quit | SPACE = start/pause | A = add variety", (10, h-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('Data Collection - IMPROVED HAND DETECTION', frame)
        
        # Auto-capture when active AND hand detected
        if capturing and hand_detected:
            # Save the ORIGINAL roi without drawings
            roi_clean = cv2.flip(frame, 1)[y1:y2, x1:x2]
            
            # Apply random augmentation for 20% of images
            if np.random.random() < 0.2:
                roi_clean = add_noise_augmentation(roi_clean)
            
            filename = f'{BASE_DIR}/{gesture_name}/img_{count:04d}.jpg'
            cv2.imwrite(filename, roi_clean, [cv2.IMWRITE_JPEG_QUALITY, 95])
            count += 1
            
            # Progress indicator
            if count % 50 == 0:
                print(f"  Progress: {count}/{num_samples} ({progress}%)")
            
            time.sleep(0.03)  # Faster capture for more variety
        elif capturing and not hand_detected:
            # Show warning if trying to capture without hand
            cv2.putText(frame, "⚠ PAUSED - No hand detected!", (10, h-60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            if hand_detected or not capturing:
                capturing = not capturing
                if capturing:
                    print(f"  ▶ Auto-capture started...")
                    print(f"  💡 TIP: Slowly rotate and move your hand(s)!")
                else:
                    print(f"  ⏸ Auto-capture paused at {count}/{num_samples}")
            else:
                print("  ⚠ Cannot start - no hand detected!")
        
        elif key == ord('q'):
            print(f"  ⏹ Stopped early at {count} images")
            break
            
        elif key == ord('a'):
            # Manual reminder to add variety
            print(f"  💡 Remember: Change angle, distance, rotation!")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"  ✓ Saved {count} images to {BASE_DIR}/{gesture_name}/\n")
    return count


# Main program
print("\n" + "="*60)
print("  IMPROVED STATIC SIGN LANGUAGE DATASET COLLECTION")
print("  WITH ENHANCED HAND DETECTION (1 or 2 hands supported)")
print("="*60)
print("\n  Phrases:")
print("  • Hello, I like your perspective")
print("  • 3 × 2 = 6")
print("\n  Gestures to collect:")
for i, g in enumerate(GESTURES, 1):
    print(f"  {i}. {g}")
print("\n  300 images per gesture (increased for better accuracy)")
print("  ✨ GREEN OUTLINE shows detected hand(s)!")
print("  ✨ Supports BOTH 1 and 2 hand gestures!")
print("="*60 + "\n")


# Enhanced gesture guide
print("\n" + "="*60)
print("  DETAILED GESTURE GUIDE - Make them VERY DISTINCT!")
print("="*60)
print("""
HELLO - Open palm facing forward (1 hand), wave side to side
        → Focus: Clear palm, fingers spread

I - Point to chest with index finger (1 hand), thumb tucked
        → Focus: Clear pointing gesture, distinct from others

LIKE - Thumbs up gesture (1 hand), clear and exaggerated
        → Focus: Thumb clearly extended upward

YOUR - Point forward with index finger OR flat hand (1 hand)
        → Focus: Direction of pointing, different angle from 'I'

PERSPECTIVE - Two hands forming rectangle/frame shape (2 hands)
        → Focus: Clear frame/window shape, both hands visible

THREE - Hold up 3 fingers clearly (1 hand): index, middle, ring
        → Focus: Exactly 3 fingers, others tucked

TIMES - Two index fingers crossing to form X (2 hands)
        → Focus: Clear X shape, both fingers visible

TWO - Peace sign: V shape with index + middle finger (1 hand)
        → Focus: Clear V, distinct from THREE

EQUALS - Two flat hands horizontal and parallel (2 hands)
        → Focus: Parallel lines, both hands at same height

SIX - Touch thumb to pinky on one hand (1 hand)
        → Focus: Clear contact between thumb and pinky


CRITICAL TIPS:
• Make each gesture DRAMATICALLY different
• For 2-hand gestures (PERSPECTIVE, TIMES, EQUALS): ensure BOTH hands are clearly visible
• For 1-hand gestures: center the hand in frame
• Vary: angles (left/right tilt), distance (close/far), rotation
• Maintain good lighting throughout collection
""")
print("="*60 + "\n")


total_images = 0


for gesture in GESTURES:
    print(f"\n{'='*60}")
    print(f"  GET READY: {gesture}")
    print(f"{'='*60}")
    print("  During capture:")
    print("  ✓ Wait for GREEN OUTLINE around your hand(s)")
    print("  ✓ Move hand(s) SLOWLY around the box")
    print("  ✓ Rotate, tilt, change distance")
    print("  ✓ Keep gesture CLEAR and CONSISTENT")
    print("  ✓ Fill at least 300 images for best accuracy")
    
    # Indicate if gesture needs 1 or 2 hands
    if gesture in ['PERSPECTIVE', 'TIMES', 'EQUALS']:
        print(f"  ⚠ '{gesture}' requires 2 HANDS - ensure both are visible!")
    else:
        print(f"  ℹ '{gesture}' uses 1 HAND")
    
    print(f"{'='*60}\n")
    
    input(f"  Press ENTER when ready to collect '{gesture}'...")
    count = collect_gesture(gesture, num_samples=300)
    total_images += count
    
    # Pause between gestures
    print("  Take a 5-second break...")
    time.sleep(5)


print("\n" + "="*60)
print("  COLLECTION COMPLETE!")
print("="*60)
print(f"  Total images collected: {total_images}")
print(f"  Average per gesture: {total_images // len(GESTURES)}")
print(f"  Dataset location: {BASE_DIR}/")
print("\n  Next step: python trainmodel_improved.py")
print("="*60 + "\n")