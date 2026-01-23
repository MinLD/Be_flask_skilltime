#service/auth_service.py
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity

from .upload_service import upload_file
from ..extensions import db
from ..models.models_model import TokenBlocklist, User, UserProfile, Media
from ..services.users_service import get_user_by_email
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid

def login_with_google(token_from_frontend):
    try:
        # 1. Xác thực token với Google
        id_info = id_token.verify_oauth2_token(
            token_from_frontend,
            requests.Request(),
            current_app.config['GOOGLE_CLIENT_ID']
        )
        # 2. Lấy thông tin từ Google
        email = id_info.get('email')
        name = id_info.get('name')
        google_picture = id_info.get('picture')  # URL ảnh avatar từ Google

        # 3. Kiểm tra User tồn tại chưa
        user = User.query.filter_by(email=email).first()

        if not user:
            random_password = str(uuid.uuid4())

            user = User(
                email=email,
                status='active',
                wallet_balance=3  # Default value
            )
            user.set_password(random_password)  # Hash mật khẩu

            # B. Tạo UserProfile tương ứng
            new_profile = UserProfile(
                fullname=name,
                is_online=True,
                user=user
            )
            if google_picture:
                cloud_data = upload_file(google_picture)
                if not cloud_data:
                    raise ValueError("Failed to upload file to Cloud")
                if user.profile.avatar:
                    user.profile.avatar.public_id = cloud_data['public_id']
                    user.profile.avatar.secure_url = cloud_data['secure_url']
                    user.profile.avatar.resource_type = cloud_data['resource_type']
                else:
                    new_media = Media(
                        public_id=cloud_data['public_id'],
                        secure_url=cloud_data['secure_url'],
                        resource_type=cloud_data['resource_type'],
                        profile_avatar=user.profile
                    )
                    db.session.add(new_media)



            db.session.add(user)
            db.session.add(new_profile)
            db.session.commit()

        else:

            if user.profile:
                user.profile.is_online = True
                db.session.commit()

        # 4. Tạo JWT Token (Identity là UUID string)
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # 5. Chuẩn bị dữ liệu trả về (Flatten dữ liệu từ 2 bảng)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    except ValueError:
        raise ValueError("Invalid Google Token")
    except Exception as e:
        db.session.rollback()  # Rollback nếu có lỗi DB
        raise e
def logout():
    jwt_payload = get_jwt()
    jti = jwt_payload["jti"]
    token = TokenBlocklist(jti=jti)
    db.session.add(token)
    db.session.commit()
def whoami():
    claims = get_jwt()
    return claims
def refresh_token():
        identity = get_jwt_identity()
        user = User.query.get(identity)
        if not user:
            raise ValueError ("User not found")

        user_roles = [role.name for role in user.roles]
        additional_claims = {"roles": user_roles}

        new_access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        return new_access_token


def generate_tokens(data):
        user = get_user_by_email(email=data.email)
        if not user:
            raise ValueError("Account not found")

        if user and user.check_password(password=data.password):
            user_roles = [role.name for role in user.roles]
            additional_claims = {"roles": user_roles}
            access_token = create_access_token(
            identity=str(user.id), 
            additional_claims=additional_claims
        )
            refresh_token = create_refresh_token(identity=user.id)
            return access_token, refresh_token

        raise ValueError("Invalid email or password")