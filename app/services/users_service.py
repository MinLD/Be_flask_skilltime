# service/users_service.py


from ..models.models_model import User, UserProfile, Role, Media
from ..extensions import db
from .role_service import get_role_by_name
from ..schemas.schemas import UserSchema
from ..services.upload_service import upload_file
from sqlalchemy import  or_

import re
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9]+$")

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_by_id(user_id):
    return User.query.filter_by(id=user_id).first()


def get_email_profile(email):
    return UserProfile.query.filter_by(email=email).first()

def save(data):
    db.session.add(data)
    db.session.commit()
    
def delete(data):
    db.session.delete(data)
    db.session.commit()
def model_search_user(data, page, per_page):
    search_query = data.get('keyword')
    if not search_query:
        return None, "Thiếu thông tin bắt buộc"
    search_pattern = f"%{search_query}%"
    try:
        paginated_result = User.query.join(UserProfile).filter(
            or_(
                UserProfile.phone.ilike(search_pattern),
                User.email.ilike(search_pattern),
                UserProfile.fullname.ilike(search_pattern)
            )
        ).paginate(page=page, per_page=per_page, error_out=False)
        user_data = UserSchema().dump(paginated_result.items, many=True)
        response_data = {
            "users": user_data,
            "pagination": {
                "current_page": paginated_result.page,
                "per_page": paginated_result.per_page,
                "total_items": paginated_result.total,
                "total_pages": paginated_result.pages,
                "has_next": paginated_result.has_next,
                "has_prev": paginated_result.has_prev
            }
        }
        return response_data, None
    
    except Exception as e:
        db.session.rollback() 
        return None, f"Lỗi: {e}"
   



def model_register(data):
    if User.query.filter_by(email=data.email).first():
        raise ValueError("Email already exists")
    default_role = get_role_by_name(name="user")
    if not default_role:
        raise ValueError("System error: Default role 'user' not found. Please contact admin.")
    new_profile = UserProfile(fullname=data.fullname)
    new_user = User(email=data.email)
    new_user.profile = new_profile
    new_user.set_password(data.password)
    new_user.roles.append(default_role)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def create_user_by_admin(data):
    if User.query.filter_by(email=data.email).first():
        raise ValueError(f"Email '{data.email}' is already taken")

    role_obj = get_role_by_name(name=data.role)
    if not role_obj:
        raise ValueError(f"Role '{data.role}' not found")
    new_profile = UserProfile(
        fullname=data.fullname,
        bio=data.bio,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        reputation_score=100,
        is_online=False
    )


    new_user = User(
        email=data.email,
        wallet_balance=data.wallet_balance,
        status='active'
    )

    new_user.set_password(data.password)
    new_user.profile = new_profile
    new_user.roles.append(role_obj)

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        raise ValueError("System error while saving data")
    return new_user


def update_user_profile(user_id, data, avatar_file=None):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data and not avatar_file:
        raise ValueError("No data provided for update")

    for key, value in update_data.items():

        if key == 'email':
            if value != user.email:
                if User.query.filter_by(email=value).first():
                    raise ValueError(f"Email '{value}' is already taken")
                user.email = value
        elif key in ['fullname', 'bio', 'phone', 'date_of_birth', 'social_links']:
            if not user.profile:
                user.profile = UserProfile(user_id=user.id)

            setattr(user.profile, key, value)

    if avatar_file:
        cloud_data = upload_file(avatar_file)

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

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        raise ValueError("System error while updating profile")

    return user

def admin_update_user_profile(user_id, data, avatar_file=None):
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        raise ValueError("No data provided for update")

    for key, value in update_data.items():
        if key == 'role':
            role_obj = get_role_by_name(name=value)
            if not role_obj:
                raise ValueError(f"Role '{value}' not found")
            user.roles = [role_obj]

        if key == 'email':
            if value != user.email:
                if User.query.filter_by(email=value).first():
                    raise ValueError(f"Email '{value}' is already taken")
                user.email = value
        elif key in ['wallet_balance', 'status']:
            setattr(user, key, value)
        elif key in ['fullname', 'bio', 'phone', 'date_of_birth', 'social_links', 'reputation_score']:
            if not user.profile:
                user.profile = UserProfile(user_id=user.id)


            setattr(user.profile, key, value)

    if avatar_file:
        cloud_data = upload_file(avatar_file)

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

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"DB Error: {e}")
        raise ValueError("System error while updating profile")

    return user

def delete_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    db.session.delete(user)
    db.session.commit()
    return "Delete user successfully"

def get_all_users (page , per_page):
    paginated_result = User.query.paginate(page=page, per_page=per_page)
    users_data = UserSchema().dump(paginated_result, many=True)
    return {
        "users": users_data,
        "pagination": {
            "current_page": paginated_result.page,
            "per_page": paginated_result.per_page,
            "total_items": paginated_result.total,
            "total_pages": paginated_result.pages,
            "has_next": paginated_result.has_next,
            "has_prev": paginated_result.has_prev
        }
    }

def update_password(user_id, data):
    user = get_user_by_id(user_id)
    if not user:
        return "Không tìm thấy người dùng"
    if not data or not data.get('password_old') or not data.get('password_new'):
        return "Thiếu thông tin mật khẩu cũ hoặc mật khẩu mới"
    password_old = data.get('password_old')
    password_new = data.get('password_new')
    if not user.check_password(password=password_old):
        return "Mật khẩu cũ không đúng"

    user.set_password(password_new)
    db.session.commit()
    
    return None 

def model_get_user_stats():
    from sqlalchemy import func, extract, and_
    from datetime import datetime, date
    try:
        # 1. Tổng số user
        total_users = User.query.count()

        # 2. Số user đang hoạt động (is_active=True)
        active_users = User.query.filter_by(is_active=True).count()

        # 3. Số user mới đăng ký trong HÔM NAY
        today = date.today()
        new_users_today = User.query.filter(
            func.date(User.created_at) == today
        ).count()

        # 4. Dữ liệu vẽ biểu đồ: Số user đăng ký theo từng tháng trong năm nay
        current_year = datetime.now().year
        
        # Query: Chọn Tháng, Đếm số User -> Group By Tháng
        monthly_stats = db.session.query(
            extract('month', User.created_at).label('month'),
            func.count(User.id).label('count')
        ).filter(
            extract('year', User.created_at) == current_year
        ).group_by(
            extract('month', User.created_at)
        ).order_by('month').all()

        # Chuyển đổi dữ liệu query thành list dictionary để trả về JSON
        # Khởi tạo mảng 12 tháng với giá trị 0
        chart_data = [{"month": i, "users": 0} for i in range(1, 13)]
        
        # Gán dữ liệu thật vào
        for stat in monthly_stats:
            # stat.month là float hoặc int tùy database, ép kiểu cho chắc
            month_index = int(stat.month) - 1 
            chart_data[month_index]["users"] = stat.count

        return ({
            "summary": {
                "total": total_users,
                "active": active_users,
                "inactive": total_users - active_users,
                "new_today": new_users_today
            },
            "chart_data": chart_data
        }), None

    except Exception as e:
        print(e)
        return None, f"Lỗi: {e}"