from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Vote(db.Model):
    """Vote model for storing user votes on novel chapters"""
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(44), nullable=False)
    novel_id = db.Column(db.Integer, nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    option_id = db.Column(db.Integer, nullable=False)
    signature = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vote {self.id} by {self.wallet_address} for chapter {self.chapter_number}>' 