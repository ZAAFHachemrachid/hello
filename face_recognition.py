import cv2
import os
import numpy as np
from datetime import datetime
from collections import deque
from src.database.db_operations import DatabaseOperations
from src.utils.camera_controls import CameraControls

class FaceRecognitionSystem:
    def __init__(self):
        self.db = DatabaseOperations()
        # Initialize LBPH face recognizer with optimized parameters
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2,
            neighbors=12,
            grid_x=10,
            grid_y=10
        )
        self.known_names = {}
        self.samples_per_user = {}
        self.current_place_id = 1
        self.recognition_history = deque(maxlen=10)  # Store last 10 recognitions for smoothing
        self.load_known_faces()

    def preprocess_face(self, face_img):
        """Preprocess face image for better recognition"""
        try:
            # Convert to grayscale if needed
            if len(face_img.shape) == 3:
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = face_img

            # Resize to standard size
            face_resized = cv2.resize(gray, (256, 256))
            
            # Apply histogram equalization for lighting normalization
            face_normalized = cv2.equalizeHist(face_resized)
            
            return face_normalized
        except Exception as e:
            print(f"Error preprocessing face: {e}")
            return None

    def load_known_faces(self):
        """Load and train face recognizer with known face samples"""
        users = self.db.get_all_users()
        faces = []
        labels = []
        label_names = {}
        samples_count = {}
        
        for idx, user in enumerate(users):
            face_samples = self.db.get_user_face_samples(user.id)
            label_names[idx] = user.name
            samples_count[idx] = 0
            
            for sample in face_samples:
                if os.path.exists(sample.image_path):
                    image = cv2.imread(sample.image_path)
                    if image is not None:
                        # Preprocess face sample
                        processed_face = self.preprocess_face(image)
                        if processed_face is not None:
                            faces.append(processed_face)
                            labels.append(idx)
                            samples_count[idx] += 1
        
        if faces:  # Only train if we have samples
            self.face_recognizer.train(faces, np.array(labels))
            self.known_names = label_names
            self.samples_per_user = samples_count
            print(f"Trained recognizer with {len(faces)} faces from {len(self.known_names)} users")

    def calculate_confidence_score(self, distance):
        """Convert LBPH distance to a confidence percentage"""
        # LBPH returns distance (lower is better)
        # Convert to confidence score (higher is better)
        max_distance = 100  # Maximum expected distance
        confidence = max(0, min(100, (1 - distance / max_distance) * 100))
        return confidence

    def get_dynamic_threshold(self, label):
        """Calculate dynamic confidence threshold based on number of samples"""
        base_threshold = 65  # Base threshold
        sample_factor = 2    # Increase threshold by 2 for each sample
        samples = self.samples_per_user.get(label, 0)
        threshold = min(80, base_threshold + (samples * sample_factor))
        return threshold

    def smooth_recognition(self, prediction):
        """Apply temporal smoothing to recognition results"""
        self.recognition_history.append(prediction)
        
        if len(self.recognition_history) >= 5:  # Need at least 5 samples for smoothing
            recent = list(self.recognition_history)
            name_counts = {}
            
            # Count occurrences of each name
            for n, _ in recent:
                name_counts[n] = name_counts.get(n, 0) + 1
            
            # Find the most common name
            max_count = max(name_counts.values())
            most_common = [n for n, count in name_counts.items() if count == max_count]
            
            # Return most common name if it appears more than 40% of the time
            if max_count > len(recent) * 0.4:
                # Get average confidence for the most common name
                confidences = [conf for name, conf in recent if name == most_common[0]]
                avg_confidence = sum(confidences) / len(confidences)
                return most_common[0], avg_confidence
        
        return prediction

    def recognize_face(self, face_img):
        """Recognize a face using enhanced recognition process"""
        # Preprocess the face
        processed_face = self.preprocess_face(face_img)
        if processed_face is None:
            return "unknown", 0
        
        try:
            # Predict the label and get distance
            label, distance = self.face_recognizer.predict(processed_face)
            
            # Convert distance to confidence score (0-100)
            confidence = self.calculate_confidence_score(distance)
            
            # Get dynamic threshold based on number of samples
            threshold = self.get_dynamic_threshold(label)
            
            # Check if prediction meets confidence threshold
            if confidence > threshold:
                name = self.known_names.get(label, "unknown")
                # Apply temporal smoothing
                smoothed_name, smoothed_confidence = self.smooth_recognition((name, confidence))
                return smoothed_name, smoothed_confidence
            else:
                return "unknown", confidence
                
        except Exception as e:
            print(f"Error during face recognition: {e}")
            return "unknown", 0

    def save_recognition_event(self, name, face_img, confidence):
        """Save recognition event to database with confidence score"""
        if name != "unknown":
            # Find user ID by name
            users = self.db.get_all_users()
            user_id = None
            for user in users:
                if user.name == name:
                    user_id = user.id
                    break
            
            if user_id:
                # Save the face image
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"data/recognition_events/{name}_{timestamp}.jpg"
                cv2.imwrite(image_path, face_img)
                
                # Create recognition event with confidence score
                self.db.add_recognition_event(user_id, self.current_place_id, image_path, confidence)

    def run(self):
        """Run the face recognition system"""
        # Create directories if they don't exist
        os.makedirs("data/recognition_events", exist_ok=True)
        
        # Initialize camera controls
        camera = CameraControls()
        camera.set_capture_callback(lambda filename, _: print(f"Photo captured: {filename}"))
        
        if not camera.start():
            print("Error: Could not start camera.")
            return
            
        # Load the face detection cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        # Set window properties
        cv2.namedWindow("Face Recognition System", cv2.WINDOW_NORMAL)
        
        # Show keyboard shortcuts
        print("\nKeyboard Shortcuts:")
        print("SPACE: Capture photo")
        print("R: Reset/Retake")
        print("ESC: Exit")
        
        while camera.is_running:
            frame = camera.read_frame()
            if frame is None:
                continue
                
            # Convert frame to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
            # Process detected faces
            detected_someone = False
            for (x, y, w, h) in faces:
                detected_someone = True
                # Extract face region
                face_img = frame[y:y+h, x:x+w]
                
                # Recognize face
                name, confidence = self.recognize_face(face_img)
                
                # Draw rectangle and name
                color = (0, 255, 0) if name != "unknown" else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                
                # Display name and confidence
                display_text = f"{name} ({confidence:.1f}%)"
                cv2.putText(frame, display_text, (x, y-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Show capture hint if face detected
            if detected_someone:
                cv2.putText(frame, "Press SPACE to capture", (10, frame.shape[0] - 20),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display the frame
            camera.show_preview(frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if not camera.handle_key(key):
                break
                
            # Handle photo capture
            if key == ord(' ') and detected_someone:
                for (x, y, w, h) in faces:
                    face_img = frame[y:y+h, x:x+w]
                    name, confidence = self.recognize_face(face_img)
                    self.save_recognition_event(name, face_img, confidence)
        
        camera.stop()

def main():
    face_system = FaceRecognitionSystem()
    face_system.run()

if __name__ == "__main__":
    main()