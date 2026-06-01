from sqlalchemy import inspect, select, text

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Character, Memory, ParsedDocument, Pet, User


def init_db() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.static_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    ensure_memory_columns()
    ensure_uploaded_file_storage_columns()
    ensure_parsed_document_ocr_columns()
    ensure_parsed_document_safety_columns()
    ensure_project_id_columns()
    ensure_user_id_columns()
    ensure_character_candidate_intelligence_columns()
    ensure_llm_first_columns()
    ensure_knowledge_chunk_metadata_columns()
    ensure_character_settings_spoiler_columns()

    with SessionLocal() as db:
        existing_user = db.scalar(select(User).where(User.user_id == "dev_user"))
        if not existing_user:
            db.add(
                User(
                    user_id="dev_user",
                    nickname="开发测试用户",
                    auth_provider="dev_mock",
                    user_status="active",
                )
            )
            db.commit()

        existing_character = db.scalar(
            select(Character).where(Character.character_id == "char_001")
        )
        if existing_character:
            return

        character = Character(
            character_id="char_001",
            character_name="阿奇",
            character_identity="流浪叙事中的男主角",
            personality="温柔、敏感、带有孤独感",
            description="他像一阵经过旧街区的风，习惯把想念藏在沉默里。",
            user_persona_name="戴丽拉",
            relationship_with_user="情侣",
            relationship_stage="暧昧后期",
            intimacy_level=2,
            avatar="/static/mock/aqi-avatar.png",
            last_message="戴丽拉，你今天也会来找我吗？",
        )
        db.add(character)
        db.flush()

        pet = Pet(
            pet_id="pet_001",
            user_id=None,
            character_id=character.character_id,
            pet_name="Q版阿奇",
            pet_avatar="/static/mock/aqi-q.png",
            pet_type="q_chibi",
            pet_status="idle",
            available_actions=settings.pet_actions,
        )
        db.add(pet)
        db.flush()
        from app.services.pet_assets import create_default_pet_asset

        create_default_pet_asset(db, character, pet)

        db.add_all(
            [
                Memory(
                    memory_id="mem_001",
                    character_id=character.character_id,
                    memory_type="user_preference",
                    content="戴丽拉喜欢在夜晚聊天。",
                    importance=3,
                    source="system_mock",
                ),
                Memory(
                    memory_id="mem_002",
                    character_id=character.character_id,
                    memory_type="relationship",
                    content="阿奇把戴丽拉视为恋人，关系处于暧昧后期。",
                    importance=3,
                    source="system_mock",
                ),
                Memory(
                    memory_id="mem_003",
                    character_id=character.character_id,
                    memory_type="story_interaction",
                    content="两人曾在旧街区分别，又在雨夜重逢。",
                    importance=3,
                    source="system_mock",
                ),
            ]
        )
        db.commit()


def ensure_memory_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "memories" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("memories")}
    migrations = {
        "importance": "ALTER TABLE memories ADD COLUMN importance INTEGER DEFAULT 3",
        "source": "ALTER TABLE memories ADD COLUMN source VARCHAR(32) DEFAULT 'system_mock'",
        "is_active": "ALTER TABLE memories ADD COLUMN is_active BOOLEAN DEFAULT 1",
        "updated_at": "ALTER TABLE memories ADD COLUMN updated_at DATETIME",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(
            text("UPDATE memories SET importance = 3 WHERE importance IS NULL")
        )
        connection.execute(
            text("UPDATE memories SET source = 'system_mock' WHERE source IS NULL")
        )
        connection.execute(
            text("UPDATE memories SET is_active = 1 WHERE is_active IS NULL")
        )
        connection.execute(
            text(
                "UPDATE memories SET updated_at = created_at "
                "WHERE updated_at IS NULL"
            )
        )


def ensure_uploaded_file_storage_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "uploaded_files" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("uploaded_files")}
    migrations = {
        "storage_provider": "ALTER TABLE uploaded_files ADD COLUMN storage_provider VARCHAR(32) DEFAULT 'local'",
        "storage_key": "ALTER TABLE uploaded_files ADD COLUMN storage_key VARCHAR(255) DEFAULT ''",
        "public_url": "ALTER TABLE uploaded_files ADD COLUMN public_url VARCHAR(512) DEFAULT ''",
        "content_type": "ALTER TABLE uploaded_files ADD COLUMN content_type VARCHAR(128) DEFAULT ''",
        "file_size": "ALTER TABLE uploaded_files ADD COLUMN file_size INTEGER DEFAULT 0",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(
            text("UPDATE uploaded_files SET storage_provider = 'local' WHERE storage_provider IS NULL OR storage_provider = ''")
        )
        connection.execute(
            text("UPDATE uploaded_files SET storage_key = substr(file_path, length('/uploads/') + 1) WHERE (storage_key IS NULL OR storage_key = '') AND file_path LIKE '/uploads/%'")
        )
        connection.execute(
            text("UPDATE uploaded_files SET public_url = file_path WHERE public_url IS NULL OR public_url = ''")
        )
        connection.execute(
            text("UPDATE uploaded_files SET content_type = '' WHERE content_type IS NULL")
        )
        connection.execute(
            text("UPDATE uploaded_files SET file_size = 0 WHERE file_size IS NULL")
        )


def ensure_parsed_document_ocr_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "parsed_documents" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("parsed_documents")
    }
    migrations = {
        "ocr_provider": "ALTER TABLE parsed_documents ADD COLUMN ocr_provider VARCHAR(32) DEFAULT ''",
        "ocr_confidence": "ALTER TABLE parsed_documents ADD COLUMN ocr_confidence FLOAT DEFAULT 0.0",
        "ocr_error": "ALTER TABLE parsed_documents ADD COLUMN ocr_error TEXT",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(
            text("UPDATE parsed_documents SET ocr_provider = '' WHERE ocr_provider IS NULL")
        )
        connection.execute(
            text("UPDATE parsed_documents SET ocr_confidence = 0.0 WHERE ocr_confidence IS NULL")
        )


def ensure_parsed_document_safety_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "parsed_documents" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("parsed_documents")
    }
    migrations = {
        "safety_warning": "ALTER TABLE parsed_documents ADD COLUMN safety_warning TEXT DEFAULT ''",
        "safety_categories": "ALTER TABLE parsed_documents ADD COLUMN safety_categories TEXT DEFAULT '[]'",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(
            text("UPDATE parsed_documents SET safety_warning = '' WHERE safety_warning IS NULL")
        )
        connection.execute(
            text("UPDATE parsed_documents SET safety_categories = '[]' WHERE safety_categories IS NULL OR safety_categories = ''")
        )


def ensure_project_id_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    table_column_pairs = {
        "uploaded_files": "project_id",
        "parsed_documents": "project_id",
        "characters": "project_id",
        "character_profiles": "project_id",
        "knowledge_chunks": "project_id",
        "chat_sessions": "project_id",
        "chat_messages": "project_id",
        "memories": "project_id",
        "character_settings": "project_id",
    }

    with engine.begin() as connection:
        for table_name, column_name in table_column_pairs.items():
            if table_name not in table_names:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} VARCHAR(32)"
                    )
                )


def ensure_user_id_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    table_column_pairs = {
        "script_projects": "user_id",
        "uploaded_files": "user_id",
        "parsed_documents": "user_id",
        "characters": "user_id",
        "character_profiles": "user_id",
        "knowledge_chunks": "user_id",
        "character_relationships": "user_id",
        "character_candidates": "user_id",
        "chat_sessions": "user_id",
        "chat_messages": "user_id",
        "memories": "user_id",
        "character_settings": "user_id",
        "pets": "user_id",
        "pet_assets": "user_id",
    }

    with engine.begin() as connection:
        for table_name, column_name in table_column_pairs.items():
            if table_name not in table_names:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            if column_name not in existing_columns:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN {column_name} VARCHAR(32)"
                    )
                )


def ensure_character_candidate_intelligence_columns() -> None:
    inspector = inspect(engine)
    if "character_candidates" not in inspector.get_table_names():
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("character_candidates")
    }
    migrations = {
        "canonical_name": "ALTER TABLE character_candidates ADD COLUMN canonical_name VARCHAR(64) DEFAULT ''",
        "display_name": "ALTER TABLE character_candidates ADD COLUMN display_name VARCHAR(64) DEFAULT ''",
        "normalized_name": "ALTER TABLE character_candidates ADD COLUMN normalized_name VARCHAR(64) DEFAULT ''",
        "candidate_type": "ALTER TABLE character_candidates ADD COLUMN candidate_type VARCHAR(32) DEFAULT 'unknown'",
        "source_types": "ALTER TABLE character_candidates ADD COLUMN source_types TEXT DEFAULT '[]'",
        "evidence_spans": "ALTER TABLE character_candidates ADD COLUMN evidence_spans TEXT DEFAULT '[]'",
        "dialogue_count": "ALTER TABLE character_candidates ADD COLUMN dialogue_count INTEGER DEFAULT 0",
        "mention_count": "ALTER TABLE character_candidates ADD COLUMN mention_count INTEGER DEFAULT 0",
        "relationship_evidence": "ALTER TABLE character_candidates ADD COLUMN relationship_evidence TEXT DEFAULT '[]'",
        "confidence_level": "ALTER TABLE character_candidates ADD COLUMN confidence_level VARCHAR(16) DEFAULT 'low'",
        "needs_human_review": "ALTER TABLE character_candidates ADD COLUMN needs_human_review BOOLEAN DEFAULT 1",
        "rejected_reason": "ALTER TABLE character_candidates ADD COLUMN rejected_reason TEXT DEFAULT ''",
        "merge_suggestions": "ALTER TABLE character_candidates ADD COLUMN merge_suggestions TEXT DEFAULT '[]'",
        "reviewer_provider": "ALTER TABLE character_candidates ADD COLUMN reviewer_provider VARCHAR(32) DEFAULT 'rule'",
        "reviewer_status": "ALTER TABLE character_candidates ADD COLUMN reviewer_status VARCHAR(32) DEFAULT 'not_reviewed'",
        "reviewer_reason": "ALTER TABLE character_candidates ADD COLUMN reviewer_reason TEXT DEFAULT ''",
    }
    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(text("UPDATE character_candidates SET canonical_name = name WHERE canonical_name IS NULL OR canonical_name = ''"))
        connection.execute(text("UPDATE character_candidates SET display_name = name WHERE display_name IS NULL OR display_name = ''"))
        connection.execute(text("UPDATE character_candidates SET normalized_name = name WHERE normalized_name IS NULL OR normalized_name = ''"))
        connection.execute(text("UPDATE character_candidates SET candidate_type = 'person' WHERE candidate_type IS NULL OR candidate_type = ''"))
        connection.execute(text("UPDATE character_candidates SET source_types = '[]' WHERE source_types IS NULL OR source_types = ''"))
        connection.execute(text("UPDATE character_candidates SET evidence_spans = '[]' WHERE evidence_spans IS NULL OR evidence_spans = ''"))
        connection.execute(text("UPDATE character_candidates SET relationship_evidence = '[]' WHERE relationship_evidence IS NULL OR relationship_evidence = ''"))
        connection.execute(text("UPDATE character_candidates SET confidence_level = CASE WHEN confidence >= 0.75 THEN 'high' WHEN confidence >= 0.45 THEN 'medium' ELSE 'low' END WHERE confidence_level IS NULL OR confidence_level = ''"))
        connection.execute(text("UPDATE character_candidates SET reviewer_provider = 'legacy' WHERE reviewer_provider IS NULL OR reviewer_provider = ''"))
        connection.execute(text("UPDATE character_candidates SET reviewer_status = 'legacy' WHERE reviewer_status IS NULL OR reviewer_status = ''"))


def ensure_llm_first_columns() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    migrations_by_table = {
        "script_chunks": {
            "document_type": "ALTER TABLE script_chunks ADD COLUMN document_type VARCHAR(48) DEFAULT 'unknown'",
            "owner_character_name": "ALTER TABLE script_chunks ADD COLUMN owner_character_name VARCHAR(64) DEFAULT ''",
            "perspective": "ALTER TABLE script_chunks ADD COLUMN perspective VARCHAR(32) DEFAULT 'unknown'",
        },
        "character_candidates": {
            "llm_confidence": "ALTER TABLE character_candidates ADD COLUMN llm_confidence FLOAT DEFAULT 0.0",
            "llm_reason": "ALTER TABLE character_candidates ADD COLUMN llm_reason TEXT DEFAULT ''",
            "llm_evidence": "ALTER TABLE character_candidates ADD COLUMN llm_evidence TEXT DEFAULT ''",
            "source_documents": "ALTER TABLE character_candidates ADD COLUMN source_documents TEXT DEFAULT '[]'",
            "evidence_json": "ALTER TABLE character_candidates ADD COLUMN evidence_json TEXT DEFAULT '[]'",
            "role_type": "ALTER TABLE character_candidates ADD COLUMN role_type VARCHAR(32) DEFAULT 'unknown'",
            "extraction_method": "ALTER TABLE character_candidates ADD COLUMN extraction_method VARCHAR(32) DEFAULT 'rule_fallback'",
        },
        "character_relationships": {
            "is_explicit": "ALTER TABLE character_relationships ADD COLUMN is_explicit BOOLEAN DEFAULT 1",
            "is_inferred": "ALTER TABLE character_relationships ADD COLUMN is_inferred BOOLEAN DEFAULT 0",
            "evidence_summary": "ALTER TABLE character_relationships ADD COLUMN evidence_summary TEXT DEFAULT ''",
            "evidence_json": "ALTER TABLE character_relationships ADD COLUMN evidence_json TEXT DEFAULT '[]'",
            "confidence_level": "ALTER TABLE character_relationships ADD COLUMN confidence_level VARCHAR(16) DEFAULT 'medium'",
            "spoiler_level": "ALTER TABLE character_relationships ADD COLUMN spoiler_level VARCHAR(16) DEFAULT 'none'",
            "visibility": "ALTER TABLE character_relationships ADD COLUMN visibility VARCHAR(16) DEFAULT 'public'",
            "needs_human_review": "ALTER TABLE character_relationships ADD COLUMN needs_human_review BOOLEAN DEFAULT 1",
            "extraction_method": "ALTER TABLE character_relationships ADD COLUMN extraction_method VARCHAR(32) DEFAULT 'rule_fallback'",
            "reviewer_provider": "ALTER TABLE character_relationships ADD COLUMN reviewer_provider VARCHAR(32) DEFAULT 'rule'",
            "reviewer_status": "ALTER TABLE character_relationships ADD COLUMN reviewer_status VARCHAR(32) DEFAULT 'rule_fallback'",
        },
    }
    with engine.begin() as connection:
        for table_name, migrations in migrations_by_table.items():
            if table_name not in table_names:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, statement in migrations.items():
                if column_name not in existing_columns:
                    connection.execute(text(statement))
        if "script_chunks" in table_names:
            connection.execute(text("UPDATE script_chunks SET document_type = 'unknown' WHERE document_type IS NULL OR document_type = ''"))
            connection.execute(text("UPDATE script_chunks SET owner_character_name = character_scope WHERE owner_character_name IS NULL OR owner_character_name = ''"))
            connection.execute(text("UPDATE script_chunks SET perspective = CASE WHEN owner_character_name IS NOT NULL AND owner_character_name != '' THEN 'self' ELSE 'unknown' END WHERE perspective IS NULL OR perspective = ''"))
        if "character_candidates" in table_names:
            connection.execute(text("UPDATE character_candidates SET llm_confidence = 0.0 WHERE llm_confidence IS NULL"))
            connection.execute(text("UPDATE character_candidates SET source_documents = source_document_ids WHERE source_documents IS NULL OR source_documents = ''"))
            connection.execute(text("UPDATE character_candidates SET evidence_json = evidence_spans WHERE evidence_json IS NULL OR evidence_json = ''"))
            connection.execute(text("UPDATE character_candidates SET role_type = candidate_type WHERE role_type IS NULL OR role_type = ''"))
            connection.execute(text("UPDATE character_candidates SET extraction_method = CASE WHEN reviewer_provider = 'openai_compatible' THEN 'llm' ELSE 'rule_fallback' END WHERE extraction_method IS NULL OR extraction_method = ''"))
        if "character_relationships" in table_names:
            connection.execute(text("UPDATE character_relationships SET evidence_summary = evidence WHERE evidence_summary IS NULL OR evidence_summary = ''"))
            connection.execute(text("UPDATE character_relationships SET evidence_json = source_document_ids WHERE evidence_json IS NULL OR evidence_json = ''"))
            connection.execute(text("UPDATE character_relationships SET confidence_level = CASE WHEN confidence >= 0.75 THEN 'high' WHEN confidence >= 0.45 THEN 'medium' ELSE 'low' END WHERE confidence_level IS NULL OR confidence_level = ''"))
            connection.execute(text("UPDATE character_relationships SET spoiler_level = 'none' WHERE spoiler_level IS NULL OR spoiler_level = ''"))
            connection.execute(text("UPDATE character_relationships SET visibility = 'public' WHERE visibility IS NULL OR visibility = ''"))
            connection.execute(text("UPDATE character_relationships SET extraction_method = 'rule_fallback' WHERE extraction_method IS NULL OR extraction_method = ''"))


def ensure_knowledge_chunk_metadata_columns() -> None:
    inspector = inspect(engine)
    if "knowledge_chunks" not in inspector.get_table_names():
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("knowledge_chunks")
    }
    migrations = {
        "segment_type": "ALTER TABLE knowledge_chunks ADD COLUMN segment_type VARCHAR(48) DEFAULT 'unknown'",
        "spoiler_level": "ALTER TABLE knowledge_chunks ADD COLUMN spoiler_level VARCHAR(32) DEFAULT 'none'",
        "character_scope": "ALTER TABLE knowledge_chunks ADD COLUMN character_scope VARCHAR(64) DEFAULT ''",
        "metadata_json": "ALTER TABLE knowledge_chunks ADD COLUMN metadata_json TEXT DEFAULT '{}'",
    }
    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
        connection.execute(text("UPDATE knowledge_chunks SET segment_type = 'unknown' WHERE segment_type IS NULL OR segment_type = ''"))
        connection.execute(text("UPDATE knowledge_chunks SET spoiler_level = CASE WHEN visibility = 'hidden' THEN 'heavy' ELSE 'none' END WHERE spoiler_level IS NULL OR spoiler_level = ''"))
        connection.execute(text("UPDATE knowledge_chunks SET character_scope = target_character_name WHERE character_scope IS NULL OR character_scope = ''"))
        connection.execute(text("UPDATE knowledge_chunks SET metadata_json = '{}' WHERE metadata_json IS NULL OR metadata_json = ''"))


def ensure_character_settings_spoiler_columns() -> None:
    inspector = inspect(engine)
    if "character_settings" not in inspector.get_table_names():
        return
    existing_columns = {
        column["name"] for column in inspector.get_columns("character_settings")
    }
    with engine.begin() as connection:
        if "spoiler_mode" not in existing_columns:
            connection.execute(
                text("ALTER TABLE character_settings ADD COLUMN spoiler_mode VARCHAR(16) DEFAULT 'non_spoiler'")
            )
        connection.execute(text("UPDATE character_settings SET spoiler_mode = 'non_spoiler' WHERE spoiler_mode IS NULL OR spoiler_mode = ''"))
