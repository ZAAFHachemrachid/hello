import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import os
from datetime import datetime
from src.database.db_operations import DatabaseOperations
from face_recognition import FaceRecognitionSystem

class FaceRecognitionUI:
    def __init__(self):
        self.db = DatabaseOperations()
        self.root = tk.Tk()
        self.root.title("Face Recognition System")
        self.root.geometry("800x600")
        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI components"""
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        # Create tabs
        self.user_tab = ttk.Frame(self.notebook)
        self.place_tab = ttk.Frame(self.notebook)
        self.detection_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.user_tab, text='User Management')
        self.notebook.add(self.place_tab, text='Place Management')
        self.notebook.add(self.detection_tab, text='Face Detection')

        # Setup each tab
        self.setup_user_tab()
        self.setup_place_tab()
        self.setup_detection_tab()

    def setup_user_tab(self):
        """Set up the user management tab"""
        # User list frame
        list_frame = ttk.LabelFrame(self.user_tab, text='Users')
        list_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # User list
        self.user_list = ttk.Treeview(list_frame, 
            columns=('ID', 'Name', 'Created', 'Samples', 'Avg Confidence'),
            show='headings')
        self.user_list.heading('ID', text='ID')
        self.user_list.heading('Name', text='Name')
        self.user_list.heading('Created', text='Created')
        self.user_list.heading('Samples', text='Face Samples')
        self.user_list.heading('Avg Confidence', text='Avg Confidence')
        
        # Adjust column widths
        self.user_list.column('ID', width=50)
        self.user_list.column('Name', width=150)
        self.user_list.column('Created', width=150)
        self.user_list.column('Samples', width=100)
        self.user_list.column('Avg Confidence', width=100)
        
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
        ttk.Button(sample_frame, text='Capture Samples', command=self.capture_user_face).pack(side='left', padx=5)
        ttk.Button(sample_frame, text='View Samples', command=self.view_user_samples).pack(side='left', padx=5)

        # Refresh user list
        self.refresh_user_list()

    def capture_user_face(self):
        """Capture face samples for the selected user"""
        # Get selected user
        selection = self.user_list.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a user first")
            return
            
        user_id = self.user_list.item(selection[0])['values'][0]
        user_name = self.user_list.item(selection[0])['values'][1]
        
        try:
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not access camera")
                return
                
            sample_count = 0
            max_samples = 5
            
            while sample_count < max_samples:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Save face sample
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = f"data/face_samples/user_{user_id}_{timestamp}.png"
                cv2.imwrite(image_path, frame)
                
                # Add to database
                self.db.add_face_sample(user_id, image_path)
                sample_count += 1
                
                # Show progress
                messagebox.showinfo("Progress", f"Captured sample {sample_count}/{max_samples}")
                
            cap.release()
            self.refresh_user_list()
            messagebox.showinfo("Success", f"Captured {sample_count} samples for {user_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture samples: {str(e)}")

    def view_user_samples(self):
        """View face samples for the selected user"""
        # Get selected user
        selection = self.user_list.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a user first")
            return
            
        user_id = self.user_list.item(selection[0])['values'][0]
        user_name = self.user_list.item(selection[0])['values'][1]
        
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
        
        # Get samples
        samples = self.db.get_user_face_samples(user_id)
        if not samples:
            ttk.Label(scrollable_frame, text="No face samples found").pack(pady=20)
            return
            
        # Display samples in a grid
        row = 0
        col = 0
        for sample in samples:
            if os.path.exists(sample.image_path):
                try:
                    # Read and resize image
                    img = cv2.imread(sample.image_path)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        img = cv2.resize(img, (200, 150))
                        
                        # Convert to PhotoImage
                        photo = tk.PhotoImage(data=cv2.imencode('.png', img)[1].tobytes())
                        
                        # Create frame for image and timestamp
                        img_frame = ttk.Frame(scrollable_frame)
                        img_frame.grid(row=row, column=col, padx=5, pady=5)
                        
                        # Display image
                        label = ttk.Label(img_frame, image=photo)
                        label.image = photo  # Keep reference
                        label.pack()
                        
                        # Display timestamp
                        timestamp = os.path.basename(sample.image_path).split('_')[2].split('.')[0]
                        ttk.Label(img_frame, text=timestamp).pack()
                        
                        # Update grid position
                        col += 1
                        if col > 2:  # 3 images per row
                            col = 0
                            row += 1
                except Exception as e:
                    print(f"Error loading image {sample.image_path}: {str(e)}")

    def add_user(self):
        """Add a new user to the system"""
        name = self.user_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a user name")
            return
            
        try:
            self.db.add_user(name)
            self.user_name_var.set("")  # Clear the input
            self.refresh_user_list()    # Update the display
            messagebox.showinfo("Success", f"User '{name}' added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {str(e)}")

    def setup_place_tab(self):
        """Set up the place management tab"""
        # Place list frame
        list_frame = ttk.LabelFrame(self.place_tab, text='Places')
        list_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Place list
        self.place_list = ttk.Treeview(list_frame, 
            columns=('ID', 'Name', 'Description', 'Events', 'Avg Confidence'),
            show='headings')
        self.place_list.heading('ID', text='ID')
        self.place_list.heading('Name', text='Name')
        self.place_list.heading('Description', text='Description')
        self.place_list.heading('Events', text='Recognition Events')
        self.place_list.heading('Avg Confidence', text='Avg Confidence')
        
        # Adjust column widths
        self.place_list.column('ID', width=50)
        self.place_list.column('Name', width=150)
        self.place_list.column('Description', width=200)
        self.place_list.column('Events', width=100)
        self.place_list.column('Avg Confidence', width=100)
        
        self.place_list.pack(pady=5, padx=5, fill='both', expand=True)

        # Add place frame
        add_frame = ttk.LabelFrame(self.place_tab, text='Add New Place')
        add_frame.pack(padx=10, pady=5, fill='x')

        ttk.Label(add_frame, text='Name:').pack(side='left', padx=5)
        self.place_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.place_name_var).pack(side='left', padx=5)

        ttk.Label(add_frame, text='Description:').pack(side='left', padx=5)
        self.place_desc_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.place_desc_var).pack(side='left', padx=5)

        ttk.Button(add_frame, text='Add Place', command=self.add_place).pack(side='left', padx=5)

        # Refresh place list
        self.refresh_place_list()

    def setup_detection_tab(self):
        """Set up the face detection tab"""
        # Place selection frame
        select_frame = ttk.LabelFrame(self.detection_tab, text='Select Place')
        select_frame.pack(padx=10, pady=5, fill='x')

        ttk.Label(select_frame, text='Current Place:').pack(side='left', padx=5)
        self.place_var = tk.StringVar()
        self.place_combo = ttk.Combobox(select_frame, textvariable=self.place_var)
        self.place_combo.pack(side='left', padx=5)
        self.update_place_combo()

        # Control buttons frame
        btn_frame = ttk.Frame(self.detection_tab)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text='Start Detection', command=self.start_detection).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='View History', command=self.view_history).pack(side='left', padx=5)

    def refresh_user_list(self):
        """Refresh the user list display with confidence scores"""
        for item in self.user_list.get_children():
            self.user_list.delete(item)
        
        users = self.db.get_all_users()
        for user in users:
            samples = self.db.get_user_face_samples(user.id)
            avg_confidence = self.db.get_user_avg_confidence(user.id)
            confidence_display = f"{avg_confidence:.1f}%" if avg_confidence else "N/A"
            
            self.user_list.insert('', 'end', values=(
                user.id, 
                user.name, 
                user.created_at,
                len(samples),
                confidence_display
            ))

    def refresh_place_list(self):
        """Refresh the place list display with confidence scores"""
        for item in self.place_list.get_children():
            self.place_list.delete(item)
        
        places = self.db.get_all_places()
        for place in places:
            events = self.db.get_place_recognition_events(place.id)
            # Calculate average confidence for this place
            confidence_scores = [e.confidence_score for e in events if e.confidence_score is not None]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
            confidence_display = f"{avg_confidence:.1f}%" if avg_confidence else "N/A"
            
            self.place_list.insert('', 'end', values=(
                place.id,
                place.name,
                place.description,
                len(events),
                confidence_display
            ))

    def start_detection(self):
        """Start real-time face detection and recognition"""
        if not self.place_var.get():
            messagebox.showerror("Error", "Please select a place")
            return
            
        # Get place ID
        places = self.db.get_all_places()
        place_id = None
        for place in places:
            if place.name == self.place_var.get():
                place_id = place.id
                break
                
        if not place_id:
            messagebox.showerror("Error", "Selected place not found")
            return
            
        try:
            # Initialize face recognition system
            face_system = FaceRecognitionSystem()
            
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not access camera")
                return
                
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Perform face detection and recognition
                user_id, confidence = face_system.recognize_face(frame)
                
                if user_id:
                    # Save the recognition event image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_path = f"data/recognition_events/event_{user_id}_{timestamp}.png"
                    cv2.imwrite(image_path, frame)
                    
                    # Record the event
                    self.db.add_recognition_event(
                        user_id=user_id,
                        place_id=place_id,
                        image_path=image_path,
                        confidence_score=confidence
                    )
                    
                    # Get user name for display
                    user = self.db.get_user(user_id)
                    user_name = user.name if user else "Unknown"
                    
                    # Show recognition info on frame
                    cv2.putText(frame,
                        f"{user_name} ({confidence:.1f}%)",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                    )
                
                # Display the frame
                cv2.imshow('Face Recognition', frame)
                
                # Break loop on 'q' press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            messagebox.showerror("Error", f"Detection error: {str(e)}")
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()

    def add_place(self):
        """Add a new place to the system"""
        name = self.place_name_var.get().strip()
        description = self.place_desc_var.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Please enter a place name")
            return
            
        try:
            self.db.add_place(name, description)
            # Clear inputs
            self.place_name_var.set("")
            self.place_desc_var.set("")
            # Update displays
            self.refresh_place_list()
            self.update_place_combo()
            messagebox.showinfo("Success", f"Place '{name}' added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add place: {str(e)}")

    def update_place_combo(self):
        """Update the place selection combobox"""
        places = self.db.get_all_places()
        place_names = [place.name for place in places]
        self.place_combo['values'] = place_names
        if place_names:
            self.place_combo.set(place_names[0])

    def view_history(self):
        """View recognition history with confidence scores"""
        if not self.place_var.get():
            messagebox.showerror("Error", "Please select a place")
            return

        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Recognition History")
        history_window.geometry("800x400")

        # Create treeview
        history_list = ttk.Treeview(history_window, 
            columns=('Time', 'User', 'Place', 'Confidence', 'Image'),
            show='headings')
        history_list.heading('Time', text='Time')
        history_list.heading('User', text='User')
        history_list.heading('Place', text='Place')
        history_list.heading('Confidence', text='Confidence')
        history_list.heading('Image', text='Image Path')
        
        # Adjust column widths
        history_list.column('Time', width=150)
        history_list.column('User', width=100)
        history_list.column('Place', width=100)
        history_list.column('Confidence', width=100)
        history_list.column('Image', width=250)
        
        history_list.pack(pady=10, padx=10, fill='both', expand=True)

        # Get place ID from name
        places = self.db.get_all_places()
        place_id = None
        for place in places:
            if place.name == self.place_var.get():
                place_id = place.id
                break

        if place_id:
            # Get and display events
            events = self.db.get_place_recognition_events(place_id)
            for event in events:
                user = self.db.get_user(event.user_id)
                place = self.db.get_place(event.place_id)
                confidence_display = f"{event.confidence_score:.1f}%" if event.confidence_score else "N/A"
                
                history_list.insert('', 'end', values=(
                    event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    user.name if user else "Unknown",
                    place.name if place else "Unknown",
                    confidence_display,
                    event.image_path
                ))

    def run(self):
        """Start the UI application"""
        self.root.mainloop()

def main():
    app = FaceRecognitionUI()
    app.run()

if __name__ == "__main__":
    main()
