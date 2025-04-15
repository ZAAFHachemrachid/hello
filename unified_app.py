import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
from datetime import datetime
from src.database.db_operations import DatabaseOperations
from src.utils.camera_controls import CameraControls
from src.utils.ui_feedback import UIFeedback
from src.utils.detection import FaceDetector

class UnifiedApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Face Recognition System")
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
        self.recognition_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.user_tab, text='User Management')
        self.notebook.add(self.detection_tab, text='Face Detection')
        self.notebook.add(self.recognition_tab, text='Face Recognition')
        
        # Setup each tab
        self.setup_user_tab()
        self.setup_detection_tab()
        self.setup_recognition_tab()
        
        # Add global status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        self.status_bar.pack(side='bottom', fill='x')
        
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
        
        # Sample management frame
        sample_frame = ttk.LabelFrame(control_frame, text='Sample Management')
        sample_frame.pack(side='left', padx=5)
        ttk.Button(sample_frame, text='Capture Samples', 
                  command=self.capture_samples).pack(side='left', padx=5)
        ttk.Button(sample_frame, text='View Samples', 
                  command=self.view_samples).pack(side='left', padx=5)
        
        self.refresh_user_list()
        
    def setup_detection_tab(self):
        """Set up the detection tab"""
        # Initialize UI feedback
        self.detection_feedback = UIFeedback(self.detection_tab)
        
        # Control buttons
        btn_frame = ttk.Frame(self.detection_tab)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text='Start Detection', 
                  command=lambda: self.start_camera_mode("detection")).pack(side='left', padx=5)
                  
    def setup_recognition_tab(self):
        """Set up the recognition tab"""
        # Initialize UI feedback
        self.recognition_feedback = UIFeedback(self.recognition_tab)
        
        # Control buttons
        btn_frame = ttk.Frame(self.recognition_tab)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text='Start Recognition', 
                  command=lambda: self.start_camera_mode("recognition")).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='View History', 
                  command=self.view_history).pack(side='left', padx=5)
        
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
            self.status_var.set(f"User '{name}' added successfully")
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
        
        self.start_camera_mode("capture", user_id=user_id, user_name=user_name)
        
    def view_samples(self):
        """View samples for selected user"""
        selection = self.user_list.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a user")
            return
            
        user_id = self.user_list.item(selection[0])['values'][0]
        user_name = self.user_list.item(selection[0])['values'][1]
        
        try:
            samples = self.db.get_user_face_samples(user_id)
            if not samples:
                messagebox.showinfo("Info", "No samples found for this user")
                return
                
            # Create samples window
            samples_window = tk.Toplevel(self.root)
            samples_window.title(f"Face Samples - {user_name}")
            samples_window.geometry("800x600")
            
            # Create scrollable frame
            canvas = tk.Canvas(samples_window)
            scrollbar = ttk.Scrollbar(samples_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack scrollbar and canvas
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            # Display samples in a grid
            row = 0
            col = 0
            for sample in samples:
                if os.path.exists(sample.image_path):
                    try:
                        img = cv2.imread(sample.image_path)
                        if img is not None:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            img = cv2.resize(img, (200, 150))
                            photo = tk.PhotoImage(data=cv2.imencode('.png', img)[1].tobytes())
                            
                            # Create frame for image
                            img_frame = ttk.Frame(scrollable_frame)
                            img_frame.grid(row=row, column=col, padx=5, pady=5)
                            
                            label = ttk.Label(img_frame, image=photo)
                            label.image = photo
                            label.pack()
                            
                            # Update grid position
                            col += 1
                            if col > 2:
                                col = 0
                                row += 1
                    except Exception as e:
                        print(f"Error loading image {sample.image_path}: {str(e)}")
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load samples: {str(e)}")
            
    def start_camera_mode(self, mode, **kwargs):
        """Start camera in specified mode"""
        try:
            # Create camera window
            camera_window = tk.Toplevel(self.root)
            camera_window.title(f"Camera - {mode.title()} Mode")
            camera_window.geometry("1024x768")
            
            # Initialize UI feedback
            feedback = UIFeedback(camera_window)
            feedback.update_status(f"Starting {mode} mode...")
            
            # Initialize camera and detector
            camera = CameraControls()
            detector = FaceDetector()
            
            def on_capture(filename, image_bytes):
                # Handle capture based on mode
                if mode == "capture":
                    image_path = f"data/face_samples/user_{kwargs['user_id']}_{filename}"
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    self.db.add_face_sample(kwargs['user_id'], image_path)
                    feedback.show_capture_feedback()
                    feedback.update_status("Sample captured")
                    
                elif mode in ["detection", "recognition"]:
                    image_path = f"data/captured/{filename}"
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    feedback.show_capture_feedback()
                    feedback.update_status("Photo captured")
                    
            camera.set_capture_callback(on_capture)
            camera.set_status_callback(feedback.update_status)
            
            if not camera.start():
                messagebox.showerror("Error", "Could not access camera")
                camera_window.destroy()
                return
            
            feedback.update_status("Camera ready - Press SPACE to capture")
            
            # Sample counting for capture mode
            if mode == "capture":
                sample_count = 0
                max_samples = 5
                feedback.start_capture_session(max_samples)
            
            # Update camera preview
            def update_preview():
                if camera.is_running:
                    frame = camera.read_frame()
                    if frame is not None:
                        # Detect faces
                        faces = detector.detect_faces(frame)
                        
                        # Process based on mode
                        if mode == "recognition":
                            frame = detector.draw_faces(frame, faces)
                        else:
                            # Simple detection boxes for other modes
                            for (x, y, w, h) in faces:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            
                            # Show face count
                            cv2.putText(frame, f"Detected: {len(faces)}", (10, 30),
                                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        
                        # Show capture hint if faces detected
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
                            camera_window.destroy()
                            return
                            
                        # Update sample count in capture mode
                        if mode == "capture" and key == ord(' ') and faces:
                            nonlocal sample_count
                            sample_count += 1
                            feedback.update_capture_progress(sample_count)
                            
                            if sample_count >= max_samples:
                                feedback.update_status("Sample collection complete")
                                camera.stop()
                                camera_window.after(1000, camera_window.destroy)
                                self.refresh_user_list()
                                return
                        
                    camera_window.after(30, update_preview)
            
            update_preview()
            
            # Handle window close
            def on_closing():
                camera.stop()
                camera_window.destroy()
                if mode == "capture":
                    self.refresh_user_list()
            
            camera_window.protocol("WM_DELETE_WINDOW", on_closing)
            
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {str(e)}")
            if 'camera' in locals():
                camera.stop()
            if 'camera_window' in locals():
                camera_window.destroy()
                
    def view_history(self):
        """View recognition history"""
        try:
            # Create history window
            history_window = tk.Toplevel(self.root)
            history_window.title("Recognition History")
            history_window.geometry("800x600")
            
            # Create treeview
            history_list = ttk.Treeview(history_window, 
                columns=('Time', 'User', 'Confidence', 'Image'),
                show='headings')
            history_list.heading('Time', text='Time')
            history_list.heading('User', text='User')
            history_list.heading('Confidence', text='Confidence')
            history_list.heading('Image', text='Image')
            
            history_list.column('Time', width=150)
            history_list.column('User', width=150)
            history_list.column('Confidence', width=100)
            history_list.column('Image', width=300)
            
            history_list.pack(pady=10, padx=10, fill='both', expand=True)
            
            # Get and display events
            events = self.db.get_recognition_events()
            for event in events:
                user = self.db.get_user(event.user_id)
                confidence = f"{event.confidence_score:.1f}%" if event.confidence_score else "N/A"
                
                history_list.insert('', 0, values=(
                    event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    user.name if user else "Unknown",
                    confidence,
                    event.image_path
                ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load history: {str(e)}")
    
    def run(self):
        """Start the application"""
        # Create required directories
        os.makedirs("data/face_samples", exist_ok=True)
        os.makedirs("data/captured", exist_ok=True)
        
        # Print keyboard shortcuts
        print("\nKeyboard Shortcuts:")
        print("SPACE: Capture photo")
        print("R: Reset view")
        print("ESC: Exit camera")
        
        # Start the application
        self.root.mainloop()

def main():
    app = UnifiedApp()
    app.run()

if __name__ == "__main__":
    main()