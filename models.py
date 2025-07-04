from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "phone"
    DATE = "date"
    NUMBER = "number"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    FILE = "file"

class FormField(BaseModel):
    name: str
    type: FieldType
    label: str
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # For select, radio, checkbox
    value: Optional[str] = None
    confidence: float = 0.0  # How confident we are about the field mapping

class FormInfo(BaseModel):
    url: str
    title: str
    fields: List[FormField]
    action: Optional[str] = None  # Form submission URL
    method: str = "POST"
    parsed_at: datetime = Field(default_factory=datetime.now)

class UserProfile(BaseModel):
    user_id: str
    personal_info: Dict[str, Any] = {}
    preferences: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ChatSession(BaseModel):
    session_id: str
    user_id: str
    form_url: str
    form_info: Optional[FormInfo] = None
    missing_fields: List[str] = []
    collected_data: Dict[str, str] = {}
    status: str = "pending"  # pending, collecting, ready, completed, error
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ChatMessage(BaseModel):
    session_id: str
    message: str
    is_from_user: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)

class FormFillRequest(BaseModel):
    user_id: str
    form_url: str
    chat_platform: str  # whatsapp, imessage, etc.
    webhook_url: Optional[str] = None  # For sending responses back

class FormFillResponse(BaseModel):
    session_id: str
    success: bool
    message: str
    missing_fields: Optional[List[str]] = None
    questions: Optional[List[str]] = None