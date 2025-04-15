import os
from ui import FaceRecognitionUI

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'data',
        'data/face_samples',
        'data/recognition_events',
        'user_samples',
        'recognized_faces'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """Main entry point for the Face Recognition System"""
    # Ensure all required directories exist
    setup_directories()
    
    # Start the UI
    print("Starting Face Recognition System...")
    print("Available keyboard shortcuts:")
    print("- SPACE: Capture photo")
    print("- R: Reset/Retake photo")
    print("- ESC: Exit camera view")
    
    app = FaceRecognitionUI()
    app.run()

if __name__ == "__main__":
    main()