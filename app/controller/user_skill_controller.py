# controller / user_skill_controller
from flask import Blueprint, request

from ..utils.response import success_response, error_response
from ..services.user_skill_service import create_user_skill, get_all_skill, update_user_skill, delete_user_skill
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..schemas.user_skill_schema import UserSkillResponse, AddUserSkillRequest, UpdateUserSkillRequest

user_skill_bp = Blueprint('api/user_skills', __name__)
@user_skill_bp.route('/', methods=['POST'], strict_slashes=False)
@jwt_required()
def add_user_skill():
    current_user_id = get_jwt_identity()
    request_data = AddUserSkillRequest(**request.form.to_dict())
    avatar = request.files.get('avatar')
    req= create_user_skill(current_user_id, request_data, avatar)
    return success_response(data=UserSkillResponse().dump(req), message="Add user skill successfully", code=201)

@user_skill_bp.route('/', methods=['GET'])
@jwt_required()
def get_():
    current_user_id = get_jwt_identity()
    return success_response(data=UserSkillResponse(many= True).dump(get_all_skill(current_user_id)), message="Get user skill successfully", code=201)

@user_skill_bp.route('/<int:skill_id>', methods=['PATCH'], strict_slashes=False)
@jwt_required()
def update(skill_id):
    current_user_id = get_jwt_identity()
    request_data = request.form.to_dict()
    avatar = request.files.get('avatar')
    req = update_user_skill(current_user_id,skill_id, request_data, avatar)
    return success_response(data=UserSkillResponse().dump(req), message="Update user skill successfully", code=200)

@user_skill_bp.route('/<int:skill_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete(skill_id):
    current_user_id = get_jwt_identity()
    delete_user_skill(current_user_id, skill_id)
    return success_response(message="Delete user skill successfully", code=200)