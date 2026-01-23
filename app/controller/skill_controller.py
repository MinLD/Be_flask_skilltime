# app/controller/skill_controller.py
from flask import Blueprint, request

from ..schemas.skill_schema import SkillResponse, CreateSkillRequest,UpdateSkillRequest
from ..utils.response import success_response
from ..services.skill_service import (
    create_skill, get_all_skills, update_skill, delete_skill, search_skills)

skill_bp = Blueprint('api/skills', __name__)
@skill_bp.route('/', methods=['POST'])
def create():
    form_data = request.form.to_dict()
    req_data = CreateSkillRequest(**form_data)
    avatar = request.files.get('avatar')
    new_cat = create_skill(req_data, avatar)
    return success_response(data=SkillResponse().dump(new_cat), code=201, message="Skill created successfully")

@skill_bp.route('/', methods=['GET'])
def get_all():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    cats = get_all_skills(page, per_page)
    return success_response(data=cats, code=200, message="Skills found successfully")

@skill_bp.route('/<int:skill_id>', methods=['PATCH'])
def update(skill_id):
    form_data = request.form.to_dict()
    req_data = UpdateSkillRequest(**form_data)
    avatar_file = request.files.get('avatar')
    updated_skill = update_skill(skill_id, req_data, avatar_file)
    return success_response(data=SkillResponse().dump(updated_skill), code=200, message="Skill updated successfully")

@skill_bp.route('/<int:skill_id>', methods=['DELETE'])
def delete(skill_id):
    deleted_skill = delete_skill(skill_id)
    return success_response(data=deleted_skill, code=200, message="Skill deleted successfully")

@skill_bp.route('/search/<int:category_id>', methods=['GET'])
def search(category_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword')
    return success_response(data=search_skills(keyword,category_id,page, per_page), code=200, message="Skills found successfully")

