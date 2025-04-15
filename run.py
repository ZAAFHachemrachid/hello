#!/usr/bin/env python3
import os
import sys
import traceback
from src.database.init_database import create_directories
from src.database.db_operations import DatabaseOperations
from face_recognition import FaceRecognitionSystem

def init_system():
    """Initialize the face recognition system"""
    try:
        print("Initializing Face Recognition System...")
        
        # Check DBus availability
        try:
            import dbus
            bus = dbus.SessionBus()
            print("DBus session bus available")
            
            # Check portal service
            try:
                portal = bus.get_object('org.freedesktop.portal.Desktop',
                                      '/org/freedesktop/portal/desktop')
                print("Desktop portal service available")
            except dbus.exceptions.DBusException as e:
                print(f"Desktop portal error: {e}")
        except ImportError:
            print("DBus Python bindings not available")
        except Exception as e:
            print(f"DBus connection error: {e}")
        
        # Try different GUI backends
        gui_backends = ['GTK3', 'GTK', 'QT', 'TK']
        backend_found = False
        for backend in gui_backends:
            try:
                os.environ['OPENCV_VIDEOIO_PRIORITY_BACKEND'] = '0'  # Prefer built-in backend
                os.environ['QT_QPA_PLATFORM'] = backend.lower()
                print(f"Successfully initialized {backend} backend")
                backend_found = True
                break
            except Exception as e:
                print(f"Backend {backend} failed: {str(e)}")
                continue
                
        if not backend_found:
            print("Warning: No GUI backend was successfully initialized")
        
        # Create necessary directories
        print("Creating directories...")
        create_directories()
        
        # Initialize database
        print("Initializing database...")
        db = DatabaseOperations()
        
        # Create default place if none exists
        places = db.get_all_places()
        if not places:
            db.add_place("Default Location", "Default recognition location")
            print("Created default place")
        
        print("Initialization complete!")
        return True
        
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        traceback.print_exc()
        return False

def main():
    try:
        # Initialize system
        if not init_system():
            print("System initialization failed")
            return
        
        # Start face recognition
        print("\nStarting Face Recognition System...")
        face_system = FaceRecognitionSystem()
        face_system.run()
        
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
