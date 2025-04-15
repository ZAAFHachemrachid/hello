#!/usr/bin/env python3
import os
from src.database.init_database import create_directories
from src.database.db_operations import DatabaseOperations
from ui import FaceRecognitionUI

def init_system():
    """Initialize the face recognition system"""
    print("Initializing Face Recognition System...")
    
    # Set OpenCV backend to avoid Qt plugin issues
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    # Create necessary directories
    create_directories()
    
    # Initialize database
    db = DatabaseOperations()
    
    # Create default place if none exists
    places = db.get_all_places()
    if not places:
        db.add_place("Default Location", "Default recognition location")
        print("Created default place")
    
    print("Initialization complete!")

def main():
    # Initialize system
    init_system()
    
    # Start UI
    app = FaceRecognitionUI()
    app.run()

if __name__ == "__main__":
    main()