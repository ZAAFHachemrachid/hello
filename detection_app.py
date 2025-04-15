import tkinter as tk
from tkinter import ttk
import cv2
from src.utils.camera_controls import CameraControls
from src.utils.ui_feedback import UIFeedback
from src.utils.detection import FaceDetector

class DetectionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Detection System")
        self.root.geometry("1024x768")
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main UI components"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add UI feedback
        self.feedback = UIFeedback(self.main_frame)
        
        # Control buttons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text='Start Detection', command=self.start_detection).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Exit', command=self.root.quit).pack(side='left', padx=5)
        
    def start_detection(self):
        """Start real-time face detection"""
        try:
            # Create detection window
            detection_window = tk.Toplevel(self.root)
            detection_window.title("Face Detection")
            detection_window.geometry("1024x768")
            
            # Initialize UI feedback in detection window
            feedback = UIFeedback(detection_window)
            feedback.update_status("Starting camera...")
            
            # Initialize camera and detector
            camera = CameraControls()
            detector = FaceDetector()
            
            def on_capture(filename, image_bytes):
                """Handle photo capture"""
                feedback.show_capture_feedback()
                feedback.update_status(f"Photo saved as {filename}")
            
            camera.set_capture_callback(on_capture)
            camera.set_status_callback(feedback.update_status)
            
            if not camera.start():
                feedback.show_error("Could not start camera")
                detection_window.destroy()
                return
            
            feedback.update_status("Camera ready - Press SPACE to capture photo")
            
            # Update camera preview with detection
            def update_preview():
                if camera.is_running:
                    frame = camera.read_frame()
                    if frame is not None:
                        # Detect faces
                        faces = detector.detect_faces(frame)
                        
                        # Draw detection results
                        frame = detector.draw_faces(frame, faces)
                        
                        # Add instruction text if faces detected
                        if faces:
                            cv2.putText(frame, "Press SPACE to capture", 
                                      (10, frame.shape[0] - 20),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                                      (255, 255, 255), 2)
                        
                        # Show the frame
                        camera.show_preview(frame)
                        
                        # Handle keyboard input
                        key = cv2.waitKey(1) & 0xFF
                        if not camera.handle_key(key):
                            detection_window.destroy()
                            return
                        
                        # Update status with detection count
                        feedback.update_status(f"Detected {len(faces)} faces")
                        
                    detection_window.after(30, update_preview)
            
            update_preview()
            
            # Handle window close
            def on_closing():
                camera.stop()
                detection_window.destroy()
            
            detection_window.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            feedback.show_error(f"Detection error: {str(e)}")
            if 'camera' in locals():
                camera.stop()
            if 'detection_window' in locals():
                detection_window.destroy()
    
    def run(self):
        """Start the application"""
        print("\nKeyboard Shortcuts:")
        print("SPACE: Capture photo")
        print("R: Reset view")
        print("ESC: Exit camera")
        self.root.mainloop()

def main():
    app = DetectionApp()
    app.run()

if __name__ == "__main__":
    main()