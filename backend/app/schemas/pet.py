from pydantic import BaseModel


class PetInfo(BaseModel):
    pet_id: str
    pet_name: str
    pet_avatar: str
    pet_type: str
    pet_status: str
    available_actions: list[str]


class PetDetailResponse(BaseModel):
    character_id: str
    pet_name: str
    pet_avatar: str
    pet_status: str
    available_actions: list[str]
    intimacy_level: int


class PetActionRequest(BaseModel):
    character_id: str
    action: str


class PetActionResponse(BaseModel):
    character_id: str
    pet_name: str
    pet_status: str
    action: str
    message: str

