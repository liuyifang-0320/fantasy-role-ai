from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Character, CharacterProfile, KnowledgeChunk, ParsedDocument, Pet, UploadedFile
from app.schemas.character import CharacterGenerateRequest
from app.services.ids import next_prefixed_id
from app.services.parser import ensure_parsed_document
from app.services.profile_extractor import create_character_profile
from app.services.knowledge_chunker import rebuild_knowledge_chunks
from app.services.pet_assets import create_default_pet_asset
from app.services.projects import get_project
from app.services.script_intelligence_pipeline import run_script_intelligence_pipeline


def get_character(db: Session, character_id: str) -> Character | None:
    return db.scalar(
        select(Character)
        .options(selectinload(Character.pet))
        .where(Character.character_id == character_id)
    )


def list_characters(db: Session, user_id: str | None = None) -> list[Character]:
    statement = select(Character).options(selectinload(Character.pet))
    if user_id:
        statement = statement.where(
            or_(Character.user_id == user_id, Character.user_id.is_(None))
        )
    return list(
        db.scalars(
            statement.order_by(Character.updated_at.desc())
        )
    )


def generate_character(
    db: Session,
    payload: CharacterGenerateRequest,
    user_id: str | None = None,
) -> tuple[Character, list[ParsedDocument], CharacterProfile, list[KnowledgeChunk]]:
    uploaded_files = list(
        db.scalars(
            select(UploadedFile).where(
                UploadedFile.file_id.in_(payload.uploaded_file_ids)
            )
        )
    )
    if len(uploaded_files) != len(payload.uploaded_file_ids):
        missing_ids = set(payload.uploaded_file_ids) - {
            uploaded_file.file_id for uploaded_file in uploaded_files
        }
        missing_text = ", ".join(sorted(missing_ids))
        raise ValueError(f"Unknown uploaded_file_ids: {missing_text}")

    project_id = payload.project_id.strip() if payload.project_id else None
    if project_id and not get_project(db, project_id):
        raise ValueError("Project not found")
    if project_id:
        project = get_project(db, project_id)
        if project and user_id and project.user_id not in {user_id, None}:
            raise ValueError("Project does not belong to current user")
    if project_id:
        mismatched_file_ids = [
            uploaded_file.file_id
            for uploaded_file in uploaded_files
            if uploaded_file.project_id != project_id
        ]
        if mismatched_file_ids:
            raise ValueError(
                "Uploaded files do not belong to project: "
                + ", ".join(sorted(mismatched_file_ids))
            )
    if user_id:
        mismatched_user_file_ids = [
            uploaded_file.file_id
            for uploaded_file in uploaded_files
            if uploaded_file.user_id not in {user_id, None}
        ]
        if mismatched_user_file_ids:
            raise ValueError(
                "Uploaded files do not belong to current user: "
                + ", ".join(sorted(mismatched_user_file_ids))
            )

    character_id = next_prefixed_id(db, Character, "char")
    pet_id = next_prefixed_id(db, Pet, "pet")
    character_name = payload.target_character_name.strip()
    user_persona_name = payload.user_persona_name.strip()
    parsed_documents = [
        ensure_parsed_document(db, uploaded_file) for uploaded_file in uploaded_files
    ]
    if project_id:
        run_script_intelligence_pipeline(
            db,
            project_id=project_id,
            parsed_document_ids=[document.parsed_id for document in parsed_documents],
            options={"source": "character_generate"},
        )
    profile = create_character_profile(
        db,
        parsed_documents=parsed_documents,
        target_character_name=character_name,
        user_persona_name=user_persona_name,
        relationship_hint=payload.relationship_hint,
        project_id=project_id,
        user_id=user_id,
    )

    character = Character(
        character_id=character_id,
        user_id=user_id,
        project_id=project_id,
        character_name=character_name,
        character_identity=profile.extracted_identity,
        personality=profile.extracted_personality,
        description=profile.background_summary,
        user_persona_name=user_persona_name,
        relationship_with_user=profile.relationship_summary or payload.relationship_hint.strip(),
        relationship_stage=profile.story_stage,
        intimacy_level=1,
        avatar="/static/mock/generated-avatar.png",
        last_message=f"{user_persona_name}，我已经准备好继续这段故事了。",
    )
    db.add(character)
    db.flush()
    profile.character_id = character.character_id
    knowledge_chunks: list[KnowledgeChunk] = []
    for parsed_document in parsed_documents:
        knowledge_chunks.extend(
            rebuild_knowledge_chunks(
                db,
                parsed_document,
                target_character_name=character_name,
                user_persona_name=user_persona_name,
                character_id=character.character_id,
                project_id=project_id,
                user_id=user_id,
            )
        )

    pet = Pet(
        pet_id=pet_id,
        user_id=user_id,
        character_id=character.character_id,
        pet_name=f"Q版{character_name}",
        pet_avatar="/static/mock/generated-q.png",
        pet_type="q_chibi",
        pet_status="idle",
        available_actions=settings.pet_actions,
    )
    db.add(pet)
    db.flush()
    create_default_pet_asset(db, character, pet)
    db.commit()
    db.refresh(character)
    db.refresh(pet)
    db.refresh(profile)
    return get_character(db, character.character_id), parsed_documents, profile, knowledge_chunks
