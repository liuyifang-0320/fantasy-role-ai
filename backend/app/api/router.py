from fastapi import APIRouter

from app.api import (
    auth,
    characters,
    character_candidates,
    character_relationships,
    chat,
    files,
    image_generation,
    knowledge,
    llm,
    memory,
    ocr,
    parsed_documents,
    pet_assets,
    pets,
    profiles,
    projects,
    storage,
    system,
    safety,
    script_intelligence,
    user_data,
)


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(script_intelligence.router, prefix="/projects", tags=["script-intelligence"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(
    character_candidates.router,
    prefix="/character-candidates",
    tags=["character-candidates"],
)
api_router.include_router(
    character_relationships.router,
    prefix="/character-relationships",
    tags=["character-relationships"],
)
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(user_data.router, prefix="/user-data", tags=["user-data"])
api_router.include_router(
    image_generation.router,
    prefix="/image-generation",
    tags=["image-generation"],
)
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(
    parsed_documents.router,
    prefix="/parsed-documents",
    tags=["parsed-documents"],
)
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(pet_assets.router, prefix="/pet-assets", tags=["pet-assets"])
