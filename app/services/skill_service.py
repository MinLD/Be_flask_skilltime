# app/services/skill_service.py
from .upload_service import upload_file
from ..models.models_model import Skill, Category, Media
from  .category_service import get_category_by_id
from ..extensions import db
from ..schemas.skill_schema import SkillResponse
from sqlalchemy import  or_


def get_skill(**name):
    return Skill.query.filter_by(**name).first()

def create_skill(data, avatar_file):
    if get_skill(name = data.name):
        raise ValueError(f"Skill '{data.name}' already exists")

    category = get_category_by_id(data.category_id)
    if not category :
        raise ValueError(f"Category '{data.category_id}' already exists")

    new_skill = Skill(name=data.name, description=data.description, category_id=data.category_id)

    if avatar_file:
        cloud_data = upload_file(avatar_file)

        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")
        if new_skill.avatar:
            new_skill.avatar.public_id = cloud_data['public_id']
            new_skill.avatar.secure_url = cloud_data['secure_url']
            new_skill.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type'],
                profile_avatar=new_skill.avatar
            )
            new_skill.avatar = new_media
            db.session.add(new_media)

    try:
        db.session.add(new_skill)
        db.session.commit()
        new_skill.category_name = category.name
        return new_skill
    except Exception as e:
        db.session.rollback()
        raise e

def get_all_skills(page, per_page):
    paginated_result = Skill.query.paginate(page=page, per_page=per_page)
    req = SkillResponse().dump(paginated_result, many=True)
    return {
        "skills": req,
        "pagination": {
            "current_page": paginated_result.page,
            "per_page": paginated_result.per_page,
            "total_items": paginated_result.total,
            "total_pages": paginated_result.pages,
            "has_next": paginated_result.has_next,
            "has_prev": paginated_result.has_prev
        }
    }

def update_skill(skill_id,data, avatar_file):
    skill = get_skill(id = skill_id)
    if not skill:
        raise ValueError(f"Skill '{skill_id}' does not exist")
    update_data = data.model_dump(exclude_unset=True)
    if not update_data and not avatar_file:
        raise ValueError("No data provided for update")
    for key, value in update_data.items():
        if key == 'category_id':
            category = get_category_by_id(value)
            if not category:
                raise ValueError(f"Category '{value}' does not exist")
            skill.category_id = value
            skill.category_name = category.name
        setattr(skill, key, value)
    if avatar_file:
        cloud_data = upload_file(avatar_file)

        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")
        if skill.avatar:
            skill.avatar.public_id = cloud_data['public_id']
            skill.avatar.secure_url = cloud_data['secure_url']
            skill.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type'],
                profile_avatar=skill.avatar
            )
            skill.avatar = new_media
            db.session.add(new_media)

    try:
        db.session.commit()
        return skill
    except Exception as e:
        db.session.rollback()
        raise e

def delete_skill(skill_id):
    skill = get_skill(id = skill_id)
    if not skill:
        raise ValueError(f"Skill '{skill_id}' does not exist")
    db.session.delete(skill)
    db.session.commit()
    return "Delete skill successfully"

def search_skills(keyword, category_id, page, per_page):
    search_ = f"%{keyword}%"
    if not search_:
        raise ValueError("No search string provided")
    if not category_id:
        raise ValueError("No category id provided")
    query = Skill.query.filter_by(category_id=category_id)
    paginated_result = query.filter(
        or_(
            Skill.name.like(search_),
            Skill.description.like(search_)
        )
        ).paginate(page=page, per_page=per_page, error_out=False)
    req = SkillResponse().dump(paginated_result, many=True)
    response_data = {
        "skills": req,
        "pagination": {
            "current_page": paginated_result.page,
            "per_page": paginated_result.per_page,
            "total_items": paginated_result.total,
            "total_pages": paginated_result.pages,
            "has_next": paginated_result.has_next,
            "has_prev": paginated_result.has_prev
        }
    }
    return response_data
