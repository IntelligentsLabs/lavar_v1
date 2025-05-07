# app/models/conversation_update.py (or similar)

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
# from datetime import datetime # Optional

# --- Primitive/Shared Structures ---

class ConversationEntry(BaseModel):
    role: str
    content: str

class MessageEntry(BaseModel):
    role: str
    message: str
    time: float
    end_time: Optional[float] = Field(None, alias='endTime')
    seconds_from_start: Optional[float] = Field(None, alias='secondsFromStart')
    duration: Optional[float] = None
    source: Optional[str] = None

class ParameterProperty(BaseModel):
    description: Optional[str] = None
    type: str

class FunctionParameters(BaseModel):
    type: str = "object"
    properties: Dict[str, Union[ParameterProperty, str]]
    required: Optional[List[str]] = None

class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: FunctionParameters

# --- CORRECTED User and Character ---
class Character(BaseModel):
    age: int
    alias: str
    birthplace: str
    equipments: List[str]
    height: str
    name: str
    powers: List[str]
    super_skill: Optional[str] = Field(None, alias='superSkill')
    weakness: str

class User(BaseModel):
    username: str
    email: str
    id: Optional[str] = None
    character: Optional[Character]
    current_bg: Optional[str] = Field(None, alias='currentBg')
    notifications: Optional[List[Any]] = None # Fixed: Optional
    picture: Optional[HttpUrl] = None        # Fixed: Optional
# --- End CORRECTED User ---

class UserDataWrapper(BaseModel):
    user: User # Uses the corrected User model

class Metadata(BaseModel):
    token: str
    data: UserDataWrapper # Uses UserDataWrapper -> User

class ServerConfig(BaseModel):
    url: HttpUrl
    timeout_seconds: Optional[int] = Field(None, alias='timeoutSeconds')

class ToolFunction(BaseModel):
    name: str
    strict: Optional[bool] = None
    async_: Optional[bool] = Field(None, alias="async")
    parameters: FunctionParameters
    description: str

class Tool(BaseModel):
    id: str
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    type: str
    function: ToolFunction
    messages: Optional[List[Any]] = None
    org_id: Optional[str] = Field(None, alias='orgId')
    server: ServerConfig
    async_: bool = Field(..., alias="async")

class KnowledgeBase(BaseModel):
    file_ids: List[str] = Field(..., alias='fileIds')
    provider: str

class Voice(BaseModel):
    model: str
    voice_id: str = Field(..., alias='voiceId')
    provider: str
    input_min_characters: int = Field(..., alias='inputMinCharacters')
    input_punctuation_boundaries: List[str] = Field(..., alias='inputPunctuationBoundaries')

class Transcriber(BaseModel):
    model: str
    language: str
    numerals: bool
    provider: str
    confidence_threshold: float = Field(..., alias='confidenceThreshold')

class ModelOverrides(BaseModel):
    model: str
    messages: List[ConversationEntry]
    functions: List[FunctionDefinition]
    provider: str
    url: HttpUrl

class AssistantModelConfig(BaseModel):
    url: HttpUrl
    model: str
    tool_ids: Optional[List[str]] = Field(None, alias='toolIds')
    messages: List[ConversationEntry]
    provider: str
    max_tokens: Optional[int] = Field(None, alias='maxTokens')
    temperature: Optional[float] = None
    knowledge_base: Optional[KnowledgeBase] = Field(None, alias='knowledgeBase')
    tools: Optional[List[Tool]] = None
    functions: List[FunctionDefinition]

class Monitor(BaseModel):
    listen_url: str = Field(..., alias='listenUrl') # Allow wss://
    control_url: str = Field(..., alias='controlUrl') # Allow wss:// or https://

class Transport(BaseModel):
    provider: str
    assistant_video_enabled: bool = Field(..., alias='assistantVideoEnabled')

class AssistantOverrides(BaseModel):
    name: str
    model: ModelOverrides
    first_message: str = Field(..., alias='firstMessage')
    metadata: Metadata # Uses Metadata -> UserDataWrapper -> User (Corrected)

class CallData(BaseModel):
    id: str
    org_id: Optional[str] = Field(None, alias='orgId')
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    type: str
    monitor: Monitor
    transport: Transport
    web_call_url: Optional[HttpUrl] = Field(None, alias='webCallUrl')
    status: str
    assistant_id: Optional[str] = Field(None, alias='assistantId')
    assistant_overrides: Optional[AssistantOverrides] = Field(None, alias='assistantOverrides') # Uses AssistantOverrides -> Metadata -> User (Corrected)

class AssistantData(BaseModel):
    id: str
    org_id: Optional[str] = Field(None, alias='orgId')
    name: str
    voice: Voice
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    model: AssistantModelConfig
    recording_enabled: Optional[bool] = Field(None, alias='recordingEnabled')
    first_message: Optional[str] = Field(None, alias='firstMessage')
    end_call_function_enabled: Optional[bool] = Field(None, alias='endCallFunctionEnabled')
    transcriber: Transcriber
    silence_timeout_seconds: Optional[int] = Field(None, alias='silenceTimeoutSeconds')
    client_messages: Optional[List[str]] = Field(None, alias='clientMessages')
    server_messages: Optional[List[str]] = Field(None, alias='serverMessages')
    dial_keypad_function_enabled: Optional[bool] = Field(None, alias='dialKeypadFunctionEnabled')
    hipaa_enabled: Optional[bool] = Field(None, alias='hipaaEnabled')
    max_duration_seconds: Optional[int] = Field(None, alias='maxDurationSeconds')
    metadata: Metadata # Uses Metadata -> UserDataWrapper -> User (Corrected)
    voicemail_detection_enabled: Optional[bool] = Field(None, alias='voicemailDetectionEnabled')
    background_sound: Optional[str] = Field(None, alias='backgroundSound')
    backchanneling_enabled: Optional[bool] = Field(None, alias='backchannelingEnabled')
    background_denoising_enabled: Optional[bool] = Field(None, alias='backgroundDenoisingEnabled')
    server: ServerConfig

class Artifact(BaseModel):
    messages: List[MessageEntry] # MessageEntry already adjusted
    messages_open_a_i_formatted: Optional[List[ConversationEntry]] = Field(None, alias='messagesOpenAiFormatted')

# --- Top-Level Model ---
class ConversationUpdate(BaseModel):
    """The root model representing the entire conversation update event payload."""
    timestamp: int
    type: str = "conversation-update"
    conversation: List[ConversationEntry]
    messages: List[MessageEntry]
    messages_open_a_i_formatted: Optional[List[ConversationEntry]] = Field(None, alias='messagesOpenAiFormatted')
    artifact: Artifact
    call: CallData # Uses updated CallData
    assistant: AssistantData # Uses updated AssistantData

    class Config:
        # If you prefer automatic camelCase to snake_case conversion
        # alias_generator = lambda field_name: ''.join(word.capitalize() for word in field_name.split('_'))
        # populate_by_name = True # For Pydantic v2+ when using alias_generator
        pass