# Face Recognition System Improvements

## Current Issues
- System not properly distinguishing between different users
- All faces being recognized as the same user
- Need better accuracy in user detection

## Proposed Improvements

### 1. Face Recognition Enhancement
- Use Local Binary Pattern Histograms (LBPH) with optimized parameters
  - Radius: 2 (increased from default 1)
  - Neighbors: 12 (increased from default 8)
  - Grid X: 10 (increased from default 8)
  - Grid Y: 10 (increased from default 8)
- Add confidence threshold adjustment:
  - Implement dynamic threshold based on number of training samples
  - Default threshold: 80 (lower means stricter matching)

### 2. Training Process Enhancement
- Capture multiple face samples per user (at least 5)
- Add face alignment before training:
  - Detect eyes and align face to standard position
  - Normalize face size to 256x256 pixels
  - Apply histogram equalization for lighting normalization
- Implement data augmentation:
  - Slight rotations (±10 degrees)
  - Small scale variations (±5%)
  - Brightness/contrast adjustments

### 3. Recognition Process Improvements
- Add face quality assessment:
  - Check face resolution
  - Verify face alignment
  - Ensure good lighting conditions
- Implement temporal smoothing:
  - Track face recognition results over multiple frames
  - Use majority voting for final recognition decision
- Add confidence score display in UI

### 4. User Management Enhancements
- Add ability to retake/delete face samples
- Show face sample quality metrics
- Display recognition confidence scores
- Allow manual correction of misidentifications

## Implementation Plan

1. Update FaceRecognitionSystem class:
```python
def __init__(self):
    self.face_recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=2,
        neighbors=12,
        grid_x=10,
        grid_y=10
    )
```

2. Enhance face preprocessing:
```python
def preprocess_face(self, face_img):
    # Resize to standard size
    face_img = cv2.resize(face_img, (256, 256))
    # Convert to grayscale
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    # Apply histogram equalization
    return cv2.equalizeHist(gray)
```

3. Implement confidence threshold:
```python
def recognize_face(self, face_img):
    # Preprocess face
    processed_face = self.preprocess_face(face_img)
    # Predict with confidence
    label, confidence = self.face_recognizer.predict(processed_face)
    # Dynamic threshold based on training samples
    threshold = min(80, 65 + (self.samples_per_user.get(label, 0) * 2))
    return self.known_names.get(label, "unknown") if confidence < threshold else "unknown"
```

4. Add temporal smoothing:
```python
def smooth_recognition(self, predictions, window_size=10):
    # Use last N predictions for majority voting
    if len(predictions) >= window_size:
        recent = predictions[-window_size:]
        name, count = max(((n, recent.count(n)) for n in set(recent)), key=lambda x: x[1])
        if count > window_size // 2:
            return name
    return "unknown"
```

## Next Steps
1. Switch to Code mode to implement these improvements
2. Update UI to support new features
3. Add face sample quality metrics
4. Implement recognition history tracking