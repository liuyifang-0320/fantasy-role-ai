from fastapi import HTTPException, status

from app.models import User


def allow_legacy_null_user_data() -> bool:
    return True


def is_legacy_null_user_data(resource) -> bool:
    return getattr(resource, "user_id", None) is None


def ensure_user_can_access_resource(user: User, resource, resource_name: str = "Resource"):
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found",
        )
    resource_user_id = getattr(resource, "user_id", None)
    if resource_user_id == user.user_id:
        return resource
    if resource_user_id is None and allow_legacy_null_user_data():
        return resource
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"{resource_name} does not belong to current user",
    )


def ensure_user_can_access_project(user: User, project):
    return ensure_user_can_access_resource(user, project, "Project")


def ensure_user_can_access_character(user: User, character):
    return ensure_user_can_access_resource(user, character, "Character")


def ensure_user_can_access_file(user: User, uploaded_file):
    return ensure_user_can_access_resource(user, uploaded_file, "File")


def ensure_user_can_access_parsed_document(user: User, parsed_document):
    return ensure_user_can_access_resource(user, parsed_document, "Parsed document")


def ensure_user_can_access_memory(user: User, memory):
    return ensure_user_can_access_resource(user, memory, "Memory")


def ensure_user_can_access_pet_asset(user: User, pet_asset):
    return ensure_user_can_access_resource(user, pet_asset, "Pet asset")


def ensure_user_can_access_candidate(user: User, candidate):
    return ensure_user_can_access_resource(user, candidate, "Character candidate")


def ensure_user_can_access_relationship(user: User, relationship):
    return ensure_user_can_access_resource(user, relationship, "Character relationship")
