
from ..models.models_model import User, UserProfile
from ..extensions import db
from .role_service import get_role_by_name
from ..schemas.schemas import UserSchema
from ..services.upload_service import upload_file
from sqlalchemy import  or_

import re
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9]+$")

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

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
                User.username.ilike(search_pattern),
                UserProfile.email.ilike(search_pattern),
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
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = get_role_by_name(name='user')
        if not username or not password or not email:
            return None, "Thiếu thông tin bắt buộc hoặc thông tin rỗng (username, password, email)"
        username = username.strip()
        if " " in username:
            return None, "Username không có khoảng trắng" 
        if not USERNAME_REGEX.match(username):
            return None, "Username chỉ được chứa chữ cái (a-z), và số (0-9)"
        if get_user_by_username(username):
            return None, "Tên đăng nhập đã tồn tại"
        if get_email_profile(email):
            return None, "Email đã tồn tại"
        
        new_profile = UserProfile(email=email, avatar=None, fullname=None, bio=None, date_of_birth=None)
        new_user = User(username=username,roles=[role], profile=new_profile)
   
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        return new_user, None

def model_admin_register(data ):
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role').lower()
        fullname = data.get('fullname')
        points = data.get('points')

        roles = get_role_by_name(name=role)
        if not username or not password or not email:
            return None, "Thiếu thông tin bắt buộc hoặc thông tin rỗng (username, password, email)"
        username = username.strip()
        if " " in username:
            return None, "Username không có khoảng trắng" 
        if not USERNAME_REGEX.match(username):
            return None, "Username chỉ được chứa chữ cái (a-z), và số (0-9)"
        if get_user_by_username(username):
            return None, "Tên đăng nhập đã tồn tại"
        if get_email_profile(email):
            return None, "Email đã tồn tại"
        
        new_profile = UserProfile(email=email, avatar=None, fullname=fullname, bio=None, date_of_birth=None)
        new_user = User(username=username,roles=[roles], profile=new_profile, points=points)
   
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        return new_user, None

def update_user_profile(data, user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None, "Không tìm thấy người dùng"
    if not data:
        return None, "Thiếu thông tin bắt buộc"
    
    updatable_fields = ['email', 'fullname', 'bio', 'date_of_birth']
    for field in updatable_fields:
        if field in data and data[field] is not None:
            setattr(user.profile, field, data.get(field))
    if 'username' in data and data['username'] is not None:
        user.username = data['username']
    if 'points' in data and data['points'] is not None:
        user.points = data['points']
    if 'role' in data and data['role'] is not None:
        role = get_role_by_name(name=data['role'].lower())
        if not role:
            return None, "Không tìm thấy role"
        user.roles = [role]

    if 'avatar' in data:
        avatar_media, error = upload_file(data['avatar'], user_id)
        if error:
            return None, error
   
       
        user.profile.avatar = avatar_media

    db.session.commit()
    return user, None

def delete_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return None, "Không tìm thấy người dùng"
    db.session.delete(user)
    db.session.commit()
    return "Xóa người dùng thành công", None

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