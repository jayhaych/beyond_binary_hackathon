import os
import json
import numpy as np
import tensorflow as tf
import keras
from keras import layers, models, callbacks, optimizers
from keras.applications import MobileNetV2
from keras.applications.mobilenet_v2 import preprocess_input  # FIXED: Import preprocessing function
from keras._tf_keras.keras.preprocessing.image import ImageDataGenerator

print("="*60)
print("TRAINING STATIC GESTURE MODEL - MAXIMUM ACCURACY MODE")
print("="*60)
print(f"TensorFlow version: {tf.__version__}")
print(f"Keras version: {keras.__version__}")

# Check for GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"✓ GPU available: {len(gpus)} device(s)")
    for gpu in gpus:
        try:
            tf.config.experimental.set_memory_growth(gpu, True)
        except:
            pass
else:
    print("⚠ No GPU found - training will be slower")
print()

# Configuration - OPTIMIZED FOR ACCURACY
IMG_SIZE = 224
BATCH_SIZE = 16  # Good balance for stability
EPOCHS = 50  # Increased from 25
NUM_CLASSES = 10
GESTURES = ['HELLO', 'I', 'LIKE', 'YOUR', 'PERSPECTIVE',
            'THREE', 'TIMES', 'TWO', 'EQUALS', 'SIX']

DATASET_DIR = 'dataset_static'
MODEL_PATH = 'gesture_model_improved.keras'

# Verify dataset exists
if not os.path.exists(DATASET_DIR):
    print(f"ERROR: Dataset directory '{DATASET_DIR}' not found!")
    print("Run collectdata_improved.py first!")
    exit(1)

# Count and verify images
print("Dataset summary:")
total = 0
min_images = float('inf')
max_images = 0

for gesture in GESTURES:
    path = os.path.join(DATASET_DIR, gesture)
    if os.path.exists(path):
        count = len([f for f in os.listdir(path) 
                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        print(f"  {gesture:15s}: {count:4d} images")
        total += count
        min_images = min(min_images, count)
        max_images = max(max_images, count)
    else:
        print(f"  {gesture:15s}: MISSING!")
        exit(1)

print(f"\n  Total images: {total}")
print(f"  Min per class: {min_images}")
print(f"  Max per class: {max_images}")

if total < 2000:
    print("\n⚠️  WARNING: Low image count! Recommend 3000+ images (300 per gesture).")
    print("   Current dataset may lead to lower accuracy.")

if max_images / min_images > 1.5:
    print(f"\n⚠️  WARNING: Class imbalance detected!")
    print(f"   Ratio: {max_images/min_images:.2f}x difference between classes")
    print("   Consider collecting more images for underrepresented gestures.")

# IMPROVED Data Augmentation
# More aggressive augmentation for better generalization
train_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,  # FIXED: Use imported function
    rotation_range=40,           # Increased: hand can be rotated
    width_shift_range=0.25,      # Increased: hand position varies
    height_shift_range=0.25,     # Increased: hand position varies
    shear_range=0.2,             # Added: perspective changes
    zoom_range=0.35,             # Increased: hand distance varies
    brightness_range=[0.4, 1.6], # Wider range: different lighting
    channel_shift_range=30,      # Added: color variation
    horizontal_flip=False,       # Keep False for hand-specific gestures
    fill_mode='nearest',
    validation_split=0.2
)

# Validation data: NO augmentation, only preprocessing
val_datagen = ImageDataGenerator(
    preprocessing_function=preprocess_input,  # FIXED: Use imported function
    validation_split=0.2
)

print("\n" + "="*60)
print("Loading and augmenting data...")
print("="*60)

train_gen = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

val_gen = val_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

print(f"\nTraining samples: {train_gen.samples}")
print(f"Validation samples: {val_gen.samples}")
print(f"Classes: {train_gen.class_indices}")

# Build IMPROVED Model
print("\n" + "="*60)
print("Building ENHANCED Model Architecture")
print("="*60 + "\n")

# Option 1: MobileNetV2 (faster, good for real-time)
base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)

# Fine-tuning strategy: Unfreeze more layers for better accuracy
base_model.trainable = True

# Freeze early layers (keep generic features), unfreeze later layers (learn gesture-specific features)
# MobileNetV2 has 155 layers total
freeze_until = 100  # Freeze first 100 layers
for layer in base_model.layers[:freeze_until]:
    layer.trainable = False

print(f"Base model: MobileNetV2")
print(f"Total layers: {len(base_model.layers)}")
print(f"Trainable layers: {len([l for l in base_model.layers if l.trainable])}")

# Build enhanced classifier head
model = models.Sequential([
    # Base model
    base_model,
    
    # Global pooling
    layers.GlobalAveragePooling2D(),
    
    # First dense block
    layers.Dense(512, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01)),
    layers.BatchNormalization(),
    layers.Dropout(0.5),
    
    # Second dense block
    layers.Dense(256, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01)),
    layers.BatchNormalization(),
    layers.Dropout(0.4),
    
    # Third dense block (added for better feature extraction)
    layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.01)),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    
    # Output layer
    layers.Dense(NUM_CLASSES, activation='softmax')
], name='gesture_recognizer')

# Two-stage training approach for better accuracy

# Stage 1: Train only the classifier head
print("\n" + "="*60)
print("STAGE 1: Training classifier head (frozen base)")
print("="*60)

# Freeze base model
base_model.trainable = False

model.compile(
    optimizer=optimizers.Adam(learning_rate=0.001),  # Higher LR for initial training
    loss='categorical_crossentropy',
    metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
)

print(model.summary())

# Callbacks for stage 1
stage1_callbacks = [
    callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=7,
        restore_best_weights=True,
        verbose=1
    ),
    callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=0.00001,
        verbose=1
    ),
    callbacks.ModelCheckpoint(
        'best_model_stage1.keras',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    )
]

# Train stage 1
history_stage1 = model.fit(
    train_gen,
    epochs=15,  # Fewer epochs for stage 1
    validation_data=val_gen,
    callbacks=stage1_callbacks,
    verbose=1
)

print("\n" + "="*60)
print("STAGE 2: Fine-tuning entire model")
print("="*60)

# Unfreeze base model
base_model.trainable = True

# Freeze only early layers
for layer in base_model.layers[:freeze_until]:
    layer.trainable = False

# Recompile with lower learning rate for fine-tuning
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.0001),  # Lower LR for fine-tuning
    loss='categorical_crossentropy',
    metrics=['accuracy', keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
)

print(f"\nTrainable parameters after unfreezing: {model.count_params()}")

# Callbacks for stage 2
stage2_callbacks = [
    callbacks.EarlyStopping(
        monitor='val_accuracy',
        patience=10,
        restore_best_weights=True,
        verbose=1
    ),
    callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=4,
        min_lr=0.000001,
        verbose=1
    ),
    callbacks.ModelCheckpoint(
        MODEL_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    # Learning rate scheduler
    callbacks.LearningRateScheduler(
        lambda epoch: 0.0001 * 0.95 ** epoch,
        verbose=0
    )
]

# Train stage 2 (fine-tuning)
print("\nStarting fine-tuning...")
history_stage2 = model.fit(
    train_gen,
    epochs=EPOCHS,
    validation_data=val_gen,
    callbacks=stage2_callbacks,
    verbose=1
)

# Evaluate final model
print("\n" + "="*60)
print("FINAL EVALUATION")
print("="*60)

# Load best model
model = keras.models.load_model(MODEL_PATH)

val_loss, val_acc, val_top3 = model.evaluate(val_gen, verbose=1)

print(f"\n{'='*60}")
print(f"  ✓ Final Validation Accuracy: {val_acc*100:.2f}%")
print(f"  ✓ Top-3 Accuracy: {val_top3*100:.2f}%")
print(f"  ✓ Final Validation Loss: {val_loss:.4f}")
print(f"{'='*60}\n")

# Per-class accuracy analysis
print("Per-class prediction analysis:")
y_true = val_gen.classes
y_pred_probs = model.predict(val_gen, verbose=1)
y_pred = np.argmax(y_pred_probs, axis=1)

class_names = list(train_gen.class_indices.keys())

# Try to import sklearn for detailed metrics
try:
    from sklearn.metrics import classification_report, confusion_matrix
    
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=class_names))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_true, y_pred)
    print(cm)
    
    # Save confusion matrix
    np.save('confusion_matrix.npy', cm)
    print("✓ Confusion matrix saved to 'confusion_matrix.npy'")
except ImportError:
    print("\n⚠ sklearn not installed - skipping detailed metrics")
    print("  Install with: pip install scikit-learn")
    cm = None

# Save detailed results
results = {
    'final_val_accuracy': float(val_acc),
    'final_val_loss': float(val_loss),
    'top_3_accuracy': float(val_top3),
    'total_images': total,
    'train_samples': train_gen.samples,
    'val_samples': val_gen.samples,
    'epochs_completed': len(history_stage2.history['loss']),
    'class_mapping': {v: k for k, v in train_gen.class_indices.items()}
}

# Save model and metadata
model.save(MODEL_PATH)
print(f"\n✓ Best model saved to '{MODEL_PATH}'")

# Save class mapping
class_map = {v: k for k, v in train_gen.class_indices.items()}
with open('classes.json', 'w') as f:
    json.dump(class_map, f, indent=2)
print("✓ Class mapping saved to 'classes.json'")

# Save detailed results
with open('training_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("✓ Training results saved to 'training_results.json'")

print("\n" + "="*60)
print("TRAINING COMPLETE!")
print("="*60)
print("\nNext steps:")
print("1. Check 'training_results.json' for detailed metrics")
if cm is not None:
    print("2. Review confusion matrix to see which gestures are confused")
print("3. If accuracy is low (<85%), collect more varied data")
print("4. Test the model with: python test_model.py")
print("="*60 + "\n")