# app/services/user_skill_service.py
from .skill_service import get_skill
from .upload_service import upload_file
from ..models.models_model import SkillUser, Skill, Media
from ..extensions import db

def create_user_skill(user_id,data, avatar):
    existing = (SkillUser.query.filter_by(user_id= user_id, skill_id =data.skill_id).first())
    if existing:
        raise ValueError('You already added this skill')
    skill = get_skill(id = data.skill_id)
    if not skill:
        raise ValueError('Skill not found')


    new_user_skill = SkillUser(
        user_id=user_id,
        skill_id=data.skill_id,
        level=data.level,
        proof_link=data.proof_link,
        is_verified=False
    )
    if avatar:
        cloud_data = upload_file(avatar)

        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")
        if new_user_skill.avatar:
            new_user_skill.avatar.public_id = cloud_data['public_id']
            new_user_skill.avatar.secure_url = cloud_data['secure_url']
            new_user_skill.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type'],
                profile_avatar=new_user_skill.avatar,
            )
            db.session.add(new_media)
            new_user_skill.avatar = new_media


    try:
        db.session.add(new_user_skill)
        db.session.commit()
        return new_user_skill
    except Exception as e:
        db.session.rollback()
        raise e


def update_user_skill(user_id, id, data, avatar_file):
    skill_user = SkillUser.query.filter_by(user_id=user_id, id=id).first()

    if not skill_user:
        raise ValueError('User Skill not found')

    new_proof_link = data.get('proof_link')
    if new_proof_link:
        skill_user.proof_link = new_proof_link

    if avatar_file:
        cloud_data = upload_file(avatar_file)
        if not cloud_data:
            raise ValueError("Failed to upload file to Cloud")

        if skill_user.avatar:
            skill_user.avatar.public_id = cloud_data['public_id']
            skill_user.avatar.secure_url = cloud_data['secure_url']
            skill_user.avatar.resource_type = cloud_data['resource_type']
        else:
            new_media = Media(
                public_id=cloud_data['public_id'],
                secure_url=cloud_data['secure_url'],
                resource_type=cloud_data['resource_type']
            )
            skill_user.avatar = new_media
            db.session.add(new_media)

    try:
        db.session.commit()
        return skill_user
    except Exception as e:
        db.session.rollback()
        raise e



def get_all_skill(user_id):
    return SkillUser.query.filter_by(user_id=user_id).all()

def delete_user_skill(user_id, skill_id):
    skill_user = SkillUser.query.filter_by(user_id=user_id, id=skill_id).first()
    if not skill_user:
        raise ValueError('User Skill not found')
    db.session.delete(skill_user)
    db.session.commit()
    return skill_user
