from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity
from .users_service import get_user_by_username
from ..models.models_model import TokenBlocklist, User
from ..extensions import db





def logout():
        jwt_payload = get_jwt()
        jti = jwt_payload["jti"]
        token = TokenBlocklist(jti=jti)
        db.session.add(token)
        db.session.commit()
        return "Logged out successfully"
def whoami():
    claims = get_jwt()
    return claims
def refresh_token():
        identity = get_jwt_identity()
        user = User.query.get(identity)
        if not user:
            return None, "Không tìm thấy người dùng"

        user_roles = [role.name for role in user.roles]
        additional_claims = {"roles": user_roles}

        new_access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )
        
        return new_access_token, None


def generate_tokens(data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return None, None, "Thiếu username hoặc password"

        user = get_user_by_username(username=data.get('username'))
        if not user:
            return None, None, "Tài khoản không tồn tại"

        if user and user.check_password(password=data.get('password')):
            user_roles = [role.name for role in user.roles]
            additional_claims = {"roles": user_roles}
            access_token = create_access_token(
            identity=str(user.id), 
            additional_claims=additional_claims
        )
            refresh_token = create_refresh_token(identity=user.id)
            return access_token, refresh_token, None
        
        return None, None, "Username hoặc password không chính xác"