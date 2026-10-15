# models/user_model.py
import uuid
from datetime import datetime
from mongoengine import Document, StringField, DateTimeField


class User(Document):
    id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    email = StringField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    password = StringField(required=True)  # You should hash this in real-world apps
    role = StringField(required=True, choices=["admin", "supervisor", "superadmin"])
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "users",
        "indexes": ["username"],
    }

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at,
        }
