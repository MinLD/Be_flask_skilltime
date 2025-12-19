from ..models.models_model import Media
import cloudinary.uploader 
from ..extensions import db

def upload_file(file, current_user_id):
    from ..services.users_service import get_user_by_id

    if not file:
        return None,"Không có file nào được gửi lên"
    try:
        upload_result = cloudinary.uploader.upload(file)
    except Exception as e:
        return None, "Lỗi khi upload ảnh: " + str(e)
        
    public_id = upload_result.get('public_id')
    secure_url = upload_result.get('secure_url')
    resource_type = upload_result.get('resource_type')
    
    if not all([public_id, secure_url, resource_type]):
        return None, "Upload thất bại, kết quả trả về không đầy đủ"
    # TẠO MỘT BẢN GHI MEDIA MỚI
    new_media = Media(
        public_id=public_id,
        secure_url=secure_url,
        resource_type=resource_type,
        uploaded_by_user_id=current_user_id
    )
    user = get_user_by_id(current_user_id)
    if not user :
        return None, "Không tìm thấy người dùng"
    db.session.add(new_media)
    db.session.commit()
               

    return new_media, None