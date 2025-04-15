import cv2
import numpy as np
from src.database.db_operations import DatabaseOperations

class FaceDetector:
    def __init__(self):
        self.db = DatabaseOperations()
        # Load the pre-trained face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        # Load eye cascade for additional verification
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
    def detect_faces(self, frame):
        """Detect faces in the frame and return their coordinates"""
        if frame is None:
            return []
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Verify faces by checking for eyes
        verified_faces = []
        for (x, y, w, h) in faces:
            face_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(face_gray)
            if len(eyes) >= 1:  # At least one eye detected
                verified_faces.append((x, y, w, h))
        
        return verified_faces
        
    def compare_faces(self, face_img, reference_img):
        """Compare two face images and return similarity score"""
        # Convert images to same size
        face_img = cv2.resize(face_img, (256, 256))
        reference_img = cv2.resize(reference_img, (256, 256))
        
        # Convert to grayscale
        if len(face_img.shape) == 3:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        if len(reference_img.shape) == 3:
            reference_img = cv2.cvtColor(reference_img, cv2.COLOR_BGR2GRAY)
            
        # Calculate similarity using normalized correlation
        correlation = cv2.matchTemplate(face_img, reference_img, cv2.TM_CCORR_NORMED)[0][0]
        return correlation * 100  # Convert to percentage
    
    def find_matching_user(self, face_img, min_confidence=60):
        """Find matching user from database"""
        users = self.db.get_all_users()
        best_match = None
        best_confidence = 0
        
        for user in users:
            # Get user's face samples
            samples = self.db.get_user_face_samples(user.id)
            for sample in samples:
                try:
                    reference_img = cv2.imread(sample.image_path)
                    if reference_img is not None:
                        confidence = self.compare_faces(face_img, reference_img)
                        if confidence > best_confidence and confidence >= min_confidence:
                            best_confidence = confidence
                            best_match = user
                except Exception as e:
                    print(f"Error comparing with sample {sample.image_path}: {e}")
                    continue
        
        return best_match, best_confidence
    
    def draw_faces(self, frame, faces, show_landmarks=True):
        """Draw rectangles around detected faces and optionally show facial landmarks"""
        for (x, y, w, h) in faces:
            # Get face region
            face_img = frame[y:y+h, x:x+w]
            
            # Try to identify the face
            user, confidence = self.find_matching_user(face_img)
            
            # Draw face rectangle with color based on recognition
            color = (0, 255, 0) if user else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            if show_landmarks:
                # Get the face ROI
                face_gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                
                # Detect eyes in the face region
                eyes = self.eye_cascade.detectMultiScale(face_gray)
                
                # Draw eyes
                for (ex, ey, ew, eh) in eyes:
                    center = (x + ex + ew//2, y + ey + eh//2)
                    cv2.circle(frame, center, 2, color, 2)
            
            # Add detection/recognition text
            if user:
                text = f"{user.name} ({confidence:.1f}%)"
            else:
                text = "Unknown Face"
            
            cv2.putText(frame, text, (x, y-10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Add detection count
        cv2.putText(frame, f"Detected: {len(faces)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return frame