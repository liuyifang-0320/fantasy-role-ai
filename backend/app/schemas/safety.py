from pydantic import BaseModel


class SafetyStatusResponse(BaseModel):
    safety_mode: str
    strict_level: str
    debug_output_enabled: bool
    user_data_export_enabled: bool
    user_data_delete_enabled: bool
    privacy_contact_email: str


class SafetyDebug(BaseModel):
    user_input_action: str
    assistant_output_action: str
    matched_categories: list[str]
