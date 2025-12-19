from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from ..services.upload_service import upload_file



upload_bp = Blueprint('upload', __name__, url_prefix='/upload')
@upload_bp.route('/file', methods=['POST'])
@jwt_required()
def controller_upload_user_avatar():
    file = request.files['file']
    current_user_id = get_jwt().get('sub')
    
    return upload_file(file, current_user_id)
   
  