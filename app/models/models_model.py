# app/models/models.py
from sqlalchemy.orm import backref
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
    wallet_balance = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(50), nullable=False, default='active')
    
   
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = db.relationship('Role', secondary='role_user', back_populates='users')
    
    # 1-1 relationship: uselist=False biến nó thành object đơn thay vì list
    profile = db.relationship('UserProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')

    skill_users = db.relationship('SkillUser', back_populates='user', cascade='all, delete-orphan')

    transactions = db.relationship('Transaction', foreign_keys='Transaction.user_id', back_populates='user',
                                   lazy='dynamic')

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
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'))
    skill_user_id = db.Column(db.Integer, db.ForeignKey('skill_user.id'))



    # Relationship
    profile_avatar = db.relationship('UserProfile', back_populates='avatar', foreign_keys=[profile_avatar_id])
    category = db.relationship('Category', back_populates='avatar', foreign_keys=[category_id])
    skill = db.relationship('Skill', back_populates='avatar', foreign_keys=[skill_id])
    skill_user = db.relationship(
        'SkillUser',
        back_populates='avatar'
    , foreign_keys = [skill_user_id])



class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)

    # relationship
    avatar = db.relationship('Media', back_populates = 'category',
                             uselist = False,
                             cascade = 'all, delete-orphan',
                             lazy = 'joined'
                             )
    skills = db.relationship('Skill', back_populates = 'category')

class Skill(db.Model):
    __tablename__= 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable = False)

    # Relationship
    category = db.relationship('Category' , back_populates = 'skills')
    avatar = db.relationship('Media', back_populates='skill',
                             uselist=False,
                             cascade='all, delete-orphan',
                             lazy='joined'
                             )
    skill_users = db.relationship('SkillUser', back_populates='skill', cascade='all, delete-orphan')


class SkillUser(db.Model):
    __tablename__ ='skill_user'
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(50), nullable=False, default='beginner')
    proof_link = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    avatar = db.relationship('Media', back_populates='skill_user',uselist=False,
                             cascade='all, delete-orphan',
                             lazy='joined'
                             )
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'))
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'))
    # Đảm bảo 1 user không có 2 dòng trùng nhau cho 1 skill
    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', name='unique_user_skill'),
    )

    # RelationShip
    user = db.relationship('User', back_populates='skill_users')
    skill = db.relationship('Skill', back_populates='skill_users')




class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)  # Ví của ai biến động
    trans_type = db.Column(db.String(20), nullable=False)  # earn (cộng), spend (trừ), deposit (nạp), refund (hoàn)
    amount = db.Column(db.Integer, nullable=False)  # Số lượng thay đổi (Luôn dương)
    balance_after = db.Column(db.Integer, nullable=False)  # Số dư sau khi giao dịch (Để đối soát)
    related_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)  # Giao dịch với ai (nếu có)

    description = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # RelationShip
    user = db.relationship('User', foreign_keys=[user_id], back_populates='transactions') # <--- Biển chỉ dẫn: "Đi lối này (cột user_id) nhé!"
    related_user = db.relationship('User', foreign_keys=[related_user_id])# <--- Biển chỉ dẫn: "Đi lối kia (cột related_user_id) nhé!"


# --- 10. MatchRequest (Yêu cầu tìm người giúp) ---
class MatchRequest(db.Model):
    __tablename__ = 'match_requests'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    topic = db.Column(db.String(255), nullable=False)  # Chủ đề ngắn
    description = db.Column(db.Text, nullable=True)  # Mô tả chi tiết
    budget_credits = db.Column(db.Integer, nullable=False, default=0)  # Giá muốn trả

    status = db.Column(db.String(20), default='pending')  # pending, matched, cancelled, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('User', foreign_keys=[student_id])
    skill = db.relationship('Skill')
    session = db.relationship('MatchSession', back_populates='request', uselist=False)


# --- 11. MatchSession (Phiên kết nối Video) ---
class MatchSession(db.Model):
    __tablename__ = 'match_sessions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))

    request_id = db.Column(db.String(36), db.ForeignKey('match_requests.id'), unique=True, nullable=False)
    tutor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    room_id = db.Column(db.String(100), nullable=True)  # ID phòng chat/video (Zego/Agora)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(20), default='ongoing')  # ongoing, completed, disputed

    # Relationships
    request = db.relationship('MatchRequest', back_populates='session')
    tutor = db.relationship('User', foreign_keys=[tutor_id])