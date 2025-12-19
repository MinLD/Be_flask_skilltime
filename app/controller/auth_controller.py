from flask import Blueprint, request, jsonify
from ..utils.response import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps
from ..services.auth_service import generate_tokens, whoami, logout, refresh_token
auth_bp = Blueprint('api/auth', __name__)
def Role_required(role='admin'):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()  
        def decorator(*args, **kwargs):
            claims = get_jwt()
            print(claims)
            if role in claims.get("roles", []):
                return fn(*args, **kwargs)
            else:
                return jsonify({"message": "Admin access required!"}), 403
        return decorator
    return wrapper


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return error_response('Request body phải là JSON hoặc bị thiếu', 400)

    access_token, refresh_token, error = generate_tokens(data)

    if error:
        return error_response(error, 400)
    
    return success_response(data={'access_token': access_token, 'refresh_token': refresh_token}, code=200)

@auth_bp.route('/whoami', methods=['GET'])
@jwt_required()
def whoami_controller():
    return success_response(data=whoami(), code=200)

@auth_bp.route('/refresh', methods=['POST']) 
@jwt_required(refresh=True)
def refresh():
    new_access_token, error = refresh_token() 
    if error:
        return error_response(error, 401)
    return success_response(data={'access_token': new_access_token}, code=200)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout_controller():
    return success_response(data=logout(), code=200)

   


   

