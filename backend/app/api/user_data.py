from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import (
    Character,
    ChatMessage,
    ChatSession,
    Memory,
    PetAsset,
    ScriptProject,
    User,
)
from app.services.auth import get_current_user


router = APIRouter()


@router.get("/export")
def export_current_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.enable_user_data_export:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User data export is disabled",
        )

    projects = list(
        db.scalars(select(ScriptProject).where(ScriptProject.user_id == current_user.user_id))
    )
    characters = list(
        db.scalars(select(Character).where(Character.user_id == current_user.user_id))
    )
    memories = list(
        db.scalars(select(Memory).where(Memory.user_id == current_user.user_id))
    )

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "user": {
            "user_id": current_user.user_id,
            "nickname": current_user.nickname,
            "auth_provider": current_user.auth_provider,
            "user_status": current_user.user_status,
        },
        "projects": [
            {
                "project_id": project.project_id,
                "title": project.title,
                "project_status": project.project_status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
            }
            for project in projects
        ],
        "characters": [
            {
                "character_id": character.character_id,
                "project_id": character.project_id,
                "character_name": character.character_name,
                "relationship_with_user": character.relationship_with_user,
            }
            for character in characters
        ],
        "memories": [
            {
                "memory_id": memory.memory_id,
                "character_id": memory.character_id,
                "memory_type": memory.memory_type,
                "content": memory.content,
                "importance": memory.importance,
                "is_active": memory.is_active,
            }
            for memory in memories
        ],
        "summary": {
            "project_count": len(projects),
            "character_count": len(characters),
            "memory_count": len(memories),
            "active_memory_count": sum(1 for memory in memories if memory.is_active),
            "chat_session_count": count_user_rows(db, ChatSession, current_user.user_id),
            "chat_message_count": count_user_rows(db, ChatMessage, current_user.user_id),
            "pet_asset_count": count_user_rows(db, PetAsset, current_user.user_id),
        },
    }


@router.delete("/delete")
def delete_current_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.enable_user_data_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User data delete is disabled",
        )

    project_count = count_user_rows(db, ScriptProject, current_user.user_id)
    memory_count = count_user_rows(db, Memory, current_user.user_id)
    db.execute(
        update(ScriptProject)
        .where(ScriptProject.user_id == current_user.user_id)
        .values(project_status="archived")
    )
    db.execute(
        update(Memory)
        .where(Memory.user_id == current_user.user_id)
        .values(is_active=False)
    )
    current_user.user_status = "disabled"
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {
        "success": True,
        "message": "当前用户数据已执行开发版软删除/归档。",
        "user_id": current_user.user_id,
        "archived_project_count": project_count,
        "deactivated_memory_count": memory_count,
    }


def count_user_rows(db: Session, model, user_id: str) -> int:
    return int(
        db.scalar(select(func.count()).select_from(model).where(model.user_id == user_id))
        or 0
    )
