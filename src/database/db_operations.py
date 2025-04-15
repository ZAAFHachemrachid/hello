from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.database.models import User, FaceSample, Place, RecognitionEvent, init_db

class DatabaseOperations:
    def __init__(self):
        self.engine = init_db()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    # User operations
    def add_user(self, name):
        """Add a new user to the database"""
        user = User(name=name)
        self.session.add(user)
        self.session.commit()
        return user

    def get_user(self, user_id):
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()

    def get_all_users(self):
        """Get all users"""
        return self.session.query(User).all()

    def update_user(self, user_id, name):
        """Update user information"""
        user = self.get_user(user_id)
        if user:
            user.name = name
            self.session.commit()
        return user

    # Face Sample operations
    def add_face_sample(self, user_id, image_path):
        """Add a new face sample for a user"""
        face_sample = FaceSample(user_id=user_id, image_path=image_path)
        self.session.add(face_sample)
        self.session.commit()
        return face_sample

    def get_user_face_samples(self, user_id):
        """Get all face samples for a user"""
        return self.session.query(FaceSample).filter(FaceSample.user_id == user_id).all()

    # Place operations
    def add_place(self, name, description=""):
        """Add a new place"""
        place = Place(name=name, description=description)
        self.session.add(place)
        self.session.commit()
        return place

    def get_place(self, place_id):
        """Get place by ID"""
        return self.session.query(Place).filter(Place.id == place_id).first()

    def get_all_places(self):
        """Get all places"""
        return self.session.query(Place).all()

    def update_place(self, place_id, name=None, description=None):
        """Update place information"""
        place = self.get_place(place_id)
        if place:
            if name:
                place.name = name
            if description:
                place.description = description
            self.session.commit()
        return place

    # Recognition Event operations
    def add_recognition_event(self, user_id, place_id, image_path, confidence_score=None):
        """Record a new recognition event with confidence score"""
        event = RecognitionEvent(
            user_id=user_id,
            place_id=place_id,
            image_path=image_path,
            confidence_score=confidence_score
        )
        self.session.add(event)
        self.session.commit()
        return event

    def get_user_recognition_events(self, user_id):
        """Get all recognition events for a user"""
        return self.session.query(RecognitionEvent).filter(
            RecognitionEvent.user_id == user_id
        ).order_by(RecognitionEvent.timestamp.desc()).all()

    def get_place_recognition_events(self, place_id):
        """Get all recognition events at a place"""
        return self.session.query(RecognitionEvent).filter(
            RecognitionEvent.place_id == place_id
        ).order_by(RecognitionEvent.timestamp.desc()).all()

    def get_recent_recognition_events(self, limit=10):
        """Get recent recognition events"""
        return self.session.query(RecognitionEvent).order_by(
            RecognitionEvent.timestamp.desc()
        ).limit(limit).all()

    def get_user_avg_confidence(self, user_id):
        """Get average confidence score for a user's recognitions"""
        events = self.session.query(RecognitionEvent).filter(
            RecognitionEvent.user_id == user_id,
            RecognitionEvent.confidence_score.isnot(None)
        ).all()
        
        if not events:
            return None
            
        scores = [event.confidence_score for event in events]
        return sum(scores) / len(scores)

    def __del__(self):
        """Cleanup database session"""
        self.session.close()