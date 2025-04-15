from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    face_samples = relationship("FaceSample", back_populates="user")
    recognition_events = relationship("RecognitionEvent", back_populates="user")
    
    def __repr__(self):
        return f"<User(name='{self.name}')>"

class FaceSample(Base):
    __tablename__ = 'face_samples'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="face_samples")
    
    def __repr__(self):
        return f"<FaceSample(user_id={self.user_id}, image_path='{self.image_path}')>"

class Place(Base):
    __tablename__ = 'places'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationship
    recognition_events = relationship("RecognitionEvent", back_populates="place")
    
    def __repr__(self):
        return f"<Place(name='{self.name}')>"

class RecognitionEvent(Base):
    __tablename__ = 'recognition_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    place_id = Column(Integer, ForeignKey('places.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String, nullable=False)
    confidence_score = Column(Float)  # Added confidence score
    
    # Relationships
    user = relationship("User", back_populates="recognition_events")
    place = relationship("Place", back_populates="recognition_events")
    
    def __repr__(self):
        return f"<RecognitionEvent(user_id={self.user_id}, place_id={self.place_id}, confidence={self.confidence_score:.2f})>"

# Database initialization function
def init_db():
    engine = create_engine('sqlite:///database.sqlite')
    Base.metadata.create_all(engine)
    return engine