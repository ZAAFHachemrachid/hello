import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
from datetime import datetime
from src.database.db_operations import DatabaseOperations
from src.utils.camera_controls import CameraControls
from src.utils.ui_feedback import UIFeedback
from src.utils.detection import FaceDetector

class RecognitionApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Detection & Recognition System")
        self.root.geometry("1024x768")
        self.db = DatabaseOperations()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the main UI components"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.user_tab = ttk.Frame(self.notebook)
        self.detection_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.user_tab, text='User Management')
        self.notebook.add(self.detection_tab, text='Face Detection')
        
        self.setup_user_tab()
        self.setup_detection_tab()
        
    def setup_user_tab(self):
        """Set up the user management tab"""
        # User list frame
        list_frame = ttk.LabelFrame(self.user_tab, text='Users')
        list_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # User list
        self.user_list = ttk.Treeview(list_frame, columns=('ID', 'Name', 'Samples'),
                                     show='headings')
        self.user_list.heading('ID', text='ID')
        self.user_list.heading('Name', text='Name')
        self.user_list.heading('Samples', text='Face Samples')
        
        self.user_list.column('ID', width=50)
        self.user_list.column('Name', width=150)
        self.user_list.column('Samples', width=100)
        
        self.user_list.pack(pady=5, padx=5, fill='both', expand=True)
        
        # Control frame
        control_frame = ttk.Frame(self.user_tab)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Add user frame
        add_frame = ttk.LabelFrame(control_frame, text='Add New User')
        add_frame.pack(side='left', padx=5)
        
        ttk.Label(add_frame, text='Name:').pack(side='left', padx=5)
        self.user_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.user_name_var).pack(side='left', padx=5)
        ttk.Button(add_frame, text='Add User', command=self.add_user).pack(side='left', padx=5)
        
        # Sample capture frame
        sample_frame = ttk.LabelFrame(control_frame, text='Face Samples')
        sample_frame.pack(side='left', padx=5)
        ttk.Button(sample_frame, text='Capture Samples', 
                  command=self.capture_samples).pack(side='left', padx=5)
        
        self.refresh_user_list()
        
    def setup_detection_tab(self):
        """Set up the detection tab"""
        # Initialize UI feedback in detection tab
        self.feedback = UIFeedback(self.detection_tab)
        
        # Control buttons
        btn_frame = ttk.Frame(self.detection_tab)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text='Start Detection', 
                  command=self.start_detection).pack(side='left', padx=5)
                  
    def add_user(self):
        """Add a new user to the system"""
        name = self.user_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a user name")
            return
            
        try:
            self.db.add_user(name)
            self.user_name_var.set("")
            self.refresh_user_list()
            messagebox.showinfo("Success", f"User '{name}' added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {str(e)}")
            
    def refresh_user_list(self):
        """Refresh the user list display"""
        for item in self.user_list.get_children():
            self.user_list.delete(item)
        
        users = self.db.get_all_users()
        for user in users:
            samples = self.db.get_user_face_samples(user.id)
            self.user_list.insert('', 'end', values=(
                user.id,
                user.name,
                len(samples)
            ))
            
    def capture_samples(self):
        """Capture face samples for selected user"""
        selection = self.user_list.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
            
        user_id = self.user_list.item(selection[0])['values'][0]
        user_name = self.user_list.item(selection[0])['values'][1]
        
        try:
            # Create capture window
            capture_window = tk.Toplevel(self.root)
            capture_window.title(f"Capture Samples - {user_name}")
            capture_window.geometry("800x600")
            
            # Initialize UI feedback
            feedback = UIFeedback(capture_window)
            feedback.start_capture_session(5)  # 5 samples per user
            
            # Initialize camera and detector
            camera = CameraControls()
            detector = FaceDetector()
            
            def on_capture(filename, image_bytes):
                nonlocal sample_count
                if sample_count >= max_samples:
                    return
                    
                # Save face sample
                image_path = f"data/face_samples/user_{user_id}_{filename}"
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                
                # Add to database
                self.db.add_face_sample(user_id, image_path)
                sample_count += 1
                
                # Update progress
                feedback.update_capture_progress(sample_count)
                feedback.show_capture_feedback()
                
                if sample_count >= max_samples:
                    camera.stop()
                    capture_window.after(1000, capture_window.destroy)
                    self.refresh_user_list()
                    messagebox.showinfo("Success", 
                                      f"Captured {sample_count} samples for {user_name}")
            
            camera.set_capture_callback(on_capture)
            camera.set_status_callback(feedback.update_status)
            
            if not camera.start():
                messagebox.showerror("Error", "Could not access camera")
                capture_window.destroy()
                return
            
            sample_count = 0
            max_samples = 5
            
            feedback.update_status("Press SPACE to capture when face is detected")
            
            # Update camera preview
            def update_preview():
                if camera.is_running:
                    frame = camera.read_frame()
                    if frame is not None:
                        # Detect faces
                        faces = detector.detect_faces(frame)
                        
                        # Draw detection boxes
                        frame = detector.draw_faces(frame, faces)
                        
                        # Add sample counter
                        cv2.putText(frame, f"Samples: {sample_count}/{max_samples}",
                                  (10, frame.shape[0] - 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                  (255, 255, 255), 2)
                        
                        # Show the frame
                        camera.show_preview(frame)
                        
                        # Handle keyboard input
                        key = cv2.waitKey(1) & 0xFF
                        if not camera.handle_key(key):
                            capture_window.destroy()
                            return
                            
                    capture_window.after(30, update_preview)
            
            update_preview()
            
            # Handle window close
            def on_closing():
                camera.stop()
                capture_window.destroy()
            
            capture_window.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture samples: {str(e)}")
            
    def start_detection(self):
        """Start real-time face detection and recognition"""
        try:
            # Create detection window
            detection_window = tk.Toplevel(self.root)
            detection_window.title("Face Detection & Recognition")
            detection_window.geometry("1024x768")
            
            # Initialize UI feedback
            feedback = UIFeedback(detection_window)
            feedback.update_status("Starting face detection...")
            
            # Initialize camera and detector
            camera = CameraControls()
            detector = FaceDetector()
            
            def on_capture(filename, image_bytes):
                # Save the captured frame
                image_path = f"data/recognition_events/{filename}"
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                feedback.show_capture_feedback()
                feedback.update_status("Photo captured and saved")
            
            camera.set_capture_callback(on_capture)
            camera.set_status_callback(feedback.update_status)
            
            if not camera.start():
                messagebox.showerror("Error", "Could not access camera")
                detection_window.destroy()
                return
            
            feedback.update_status("Detection active - Press SPACE to capture photo")
            
            # Update camera preview
            def update_preview():
                if camera.is_running:
                    frame = camera.read_frame()
                    if frame is not None:
                        # Detect and recognize faces
                        faces = detector.detect_faces(frame)
                        frame = detector.draw_faces(frame, faces)
                        
                        # Show the frame
                        camera.show_preview(frame)
                        
                        # Handle keyboard input
                        key = cv2.waitKey(1) & 0xFF
                        if not camera.handle_key(key):
                            detection_window.destroy()
                            return
                            
                    detection_window.after(30, update_preview)
            
            update_preview()
            
            # Handle window close
            def on_closing():
                camera.stop()
                detection_window.destroy()
            
            detection_window.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            messagebox.showerror("Error", f"Detection error: {str(e)}")
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
    app = RecognitionApp()
    app.run()

if __name__ == "__main__":
    main()