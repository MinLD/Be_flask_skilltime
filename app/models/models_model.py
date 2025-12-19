# app/models/models.py
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
from datetime import datetime

# Bảng trung gian N-N
class Role_User(db.Model):
    __tablename__ = 'role_user'
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    # Relationships
    users = db.relationship('User', secondary='role_user', back_populates='roles')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    wallet_balance = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), nullable=False, default='active')
    
   
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = db.relationship('Role', secondary='role_user', back_populates='users')
    
    # 1-1 relationship: uselist=False biến nó thành object đơn thay vì list
    profile = db.relationship('UserProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password): 
        return check_password_hash(self.password, password)

class UserProfile(db.Model):
    __tablename__ = 'user_profile'
    # ID của profile nên là UUID giống User
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    fullname = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(10), nullable=True)
    date_of_birth = db.Column(db.DateTime(), nullable=True)
    reputation_score = db.Column(db.Float, nullable=False, default=100)
    is_online = db.Column(db.Boolean(), nullable=False, default=False)
    social_links = db.Column(db.JSON, nullable=True)

    # Foreign Key liên kết với User
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Relationship ngược lại User
    user = db.relationship('User', back_populates='profile')

    # Relationship với Media (Avatar)
    avatar = db.relationship('Media', 
                            back_populates='profile_avatar',
                            uselist=False, 
                            cascade='all, delete-orphan',
                            lazy='joined') # joined load để lấy avatar nhanh hơn

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True)
    secure_url = db.Column(db.String(255), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False, default='image')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

 
    profile_avatar_id = db.Column(db.String(36), db.ForeignKey('user_profile.id'))

    # Relationship
    profile_avatar = db.relationship('UserProfile', back_populates='avatar')