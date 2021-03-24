import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID

from jobbergate_api.main import db


class User(db.Model):
    __tablename__ = "users_user"

    id = db.Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), nullable=False, index=True, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    username = db.Column(db.String(64), index=True, nullable=False, unique=True)
    password = db.Column(db.String(248), nullable=False)
    data_joined = db.Column(db.DateTime, default=datetime.datetime.utcnow)
