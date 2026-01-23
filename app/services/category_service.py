# app/services/category_service.py
from ..models.models_model import Category, Media, Skill
from ..extensions import db
from slugify import slugify
from .upload_service import upload_file
from ..schemas.category_schema import CategoryResponse
from sqlalchemy import or_

from ..schemas.skill_schema import SkillResponse


def get_category(**name):
    return Category.query.filter_by(**name).first()

def create_category(data, avatar_file):
    if get_category(name = data.name) is not None:
        raise ValueError(f"Category '{data.name}' already exists")
    slug  = slugify(data.name)
    if get_category(slug = slug) is not None:
        raise  ValueError(f"Category '{slug}' already exists")
    new_category = Category(name=data.name, slug=slug, description=data.description)
    if avatar_file:
        cloud_data = upload_file(avatar_file)

        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")
        if new_category.avatar:
            new_category.avatar.public_id = cloud_data['public_id']
            new_category.avatar.secure_url = cloud_data['secure_url']
            new_category.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type'],
                profile_avatar=new_category.avatar
            )
            new_category.avatar = new_media
            db.session.add(new_media)
    try:
        db.session.add(new_category)
        db.session.commit()
        return new_category
    except Exception as e:
        db.session.rollback()
        raise e

def get_all_categoies(page, per_page):
    paginated_result = Category.query.paginate(page=page, per_page=per_page)
    req = CategoryResponse().dump(paginated_result, many=True)
    return {
        "categories": req,
        "pagination": {
            "current_page": paginated_result.page,
            "per_page": paginated_result.per_page,
            "total_items": paginated_result.total,
            "total_pages": paginated_result.pages,
            "has_next": paginated_result.has_next,
            "has_prev": paginated_result.has_prev
        }
    }

def get_all_skill_by_categories(category_id,page, per_page):
    category = get_category(id= category_id)
    if not category:
        raise ValueError(f"Category '{category_id}' does not exist")
    paginated_result = Skill.query.filter_by(category_id=category_id).paginate(page=page, per_page=per_page, error_out=False)
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


def get_category_by_id(cat_id):
    return Category.query.filter_by(id=cat_id).first()

def update_category(cat_id, data, avatar_file):
    cat = get_category_by_id(cat_id)
    if not cat:
        raise ValueError(f"Category '{cat_id}' does not exist")

    update_data = data.model_dump(exclude_unset=True)
    if not update_data and not avatar_file:
        raise ValueError("No data provided for update")
    for key, value in update_data.items():
        if key == 'name':
            if get_category(name=value) is not None:
                raise ValueError(f"Category '{value}' already exists")
            slug = slugify(value)
            if get_category(slug=slug) is not None:
                raise ValueError(f"Category '{slug}' already exists")
            setattr(cat, 'slug', slug)
        if key == 'description':
            setattr(cat, 'description', value)
        setattr(cat, key, value)
    if avatar_file:
        cloud_data = upload_file(avatar_file)

        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")
        if cat.avatar:
            cat.avatar.public_id = cloud_data['public_id']
            cat.avatar.secure_url = cloud_data['secure_url']
            cat.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type'],
                profile_avatar=cat.avatar
            )
            cat.avatar = new_media
            db.session.add(new_media)
    try:
        db.session.commit()
        return cat
    except Exception as e:
        db.session.rollback()
        raise e

def delete_category(cat_id):
    cat = get_category_by_id(cat_id)
    if not cat:
        raise ValueError(f"Category '{cat_id}' does not exist")
    try:
        db.session.delete(cat)
        db.session.commit()
        return cat
    except Exception as e:
        db.session.rollback()
        raise e

def search_category(keyword, page, per_page):
    if not keyword :
        raise ValueError("Keyword is required")
    search_pattern = f"%{keyword}%"
    try:
        paginated_result = Category.query.filter(
            or_(
                Category.name.ilike(search_pattern),
                Category.slug.ilike(search_pattern),
                Category.description.ilike(search_pattern)
            )
        ).paginate(page=page, per_page=per_page, error_out=False)

        req = CategoryResponse().dump(paginated_result.items, many=True)
        return {
            "categories": req,
            "pagination": {
            "current_page": paginated_result.page,
            "per_page": paginated_result.per_page,
            "total_items": paginated_result.total,
            "total_pages": paginated_result.pages,
            "has_next": paginated_result.has_next,
            "has_prev": paginated_result.has_prev
        }
        }
    except Exception as e:
        raise e






