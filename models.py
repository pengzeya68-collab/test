# Database models for TestMasterProject
from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    learning_paths = db.relationship('LearningPath', backref='user', lazy=True)
    exercises = db.relationship('Exercise', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class LearningPath(db.Model):
    __tablename__ = 'learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    estimated_hours = db.Column(db.Integer, default=10)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    exercises = db.relationship('Exercise', backref='learning_path', lazy=True)
    
    def __repr__(self):
        return f'<LearningPath {self.title}>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instructions = db.Column(db.Text)
    solution = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='easy')  # easy, medium, hard
    language = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100))  # e.g., 'variables', 'functions', 'oop'
    time_estimate = db.Column(db.Integer)  # in minutes
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learning_path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'))
    
    def __repr__(self):
        return f'<Exercise {self.title}>'

# Additional models can be added here
class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)  # 0-100
    time_spent = db.Column(db.Integer)  # in seconds
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('progress_records', lazy=True))
    exercise = db.relationship('Exercise', backref=db.backref('progress_records', lazy=True))
    
    def __repr__(self):
        return f'<Progress User:{self.user_id} Exercise:{self.exercise_id}>'