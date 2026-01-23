# app/controller/category_controller.py
from flask import Blueprint, request

from ..schemas.category_schema import CreateCategoryRequest, CategoryResponse, UpdateCategoryRequest
from ..utils.response import success_response
from ..services.category_service import (
    create_category, get_category_by_id, update_category, get_all_categoies, delete_category, search_category,
    get_all_skill_by_categories
)

category_bp = Blueprint('api/categories', __name__)
@category_bp.route('/', methods=['POST'])
def create():
    form_data = request.form.to_dict()
    req_data = CreateCategoryRequest(**form_data)
    avatar = request.files.get('avatar')
    new_cat = create_category(req_data, avatar)
    res_data = CategoryResponse().dump(new_cat)
    return success_response(data=res_data, code=201, message="Category created successfully")

@category_bp.route('/<int:cat_id>', methods=['GET'])
def get_by_id(cat_id):
    cat = get_category_by_id(cat_id)
    return success_response(data=CategoryResponse().dump(cat), code=200, message="Category found successfully")

@category_bp.route('/', methods=['GET'])
def get_all():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    cats = get_all_categoies(page, per_page)
    return success_response(data=cats, code=200, message="Categories found successfully")

@category_bp.route('/<int:cat_id>/skills', methods = ['GET'])
def get_all_skill(cat_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type = int)
    cats = get_all_skill_by_categories(cat_id,page, per_page)
    return success_response(data=cats, code=200, message="All skill by category found successfully")


@category_bp.route('/<int:cat_id>', methods=['PATCH'])
def update(cat_id):
    form_data = request.form.to_dict()
    req_data = UpdateCategoryRequest(**form_data)
    avatar = request.files.get('avatar')
    updated_cat = update_category(cat_id=cat_id, data=req_data, avatar_file=avatar)
    return success_response(data=CategoryResponse().dump(updated_cat), code=200, message="Category updated successfully")

@category_bp.route('/search', methods = ['GET'])
def search():
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    cats = search_category(keyword, page, per_page)
    return success_response(data=cats, code=200, message="Categories found successfully")


@category_bp.route('/<int:cat_id>', methods=['DELETE'])
def delete(cat_id):
    delete_category(cat_id)
    return success_response(message="Category deleted successfully", code=200, data="")