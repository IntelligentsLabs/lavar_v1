# app/models/conversation_update.py

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union

# ==============================================================================
# Sub-Models for Nested Structures
# ==============================================================================

class ToolCallFunction(BaseModel):
    name: str
    arguments: str # Arguments are often a JSON string

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: ToolCallFunction

class MessageEntry(BaseModel):
    """
    Represents a single message entry within conversation history or artifacts.
    Handles various Vapi message structures including text, tool calls, and tool results.
    """
    role: str
    time: Optional[float] = None # Present in artifact.messages, sometimes in conversation

    # For regular user/assistant text messages
    message: Optional[str] = None # Vapi often uses 'message' for content
    content: Optional[str] = None # OpenAI uses 'content'; tool results also use 'content'

    # For assistant messages requesting tool calls
    tool_calls: Optional[List[ToolCall]] = Field(None, alias="toolCalls")

    # For messages with role 'tool' (results of tool calls)
    tool_call_id: Optional[str] = Field(None, alias="toolCallId")
    name: Optional[str] = None # Name of the function for role 'tool' messages

    # Vapi specific timing/source fields (often in artifact.messages)
    end_time: Optional[float] = Field(None, alias='endTime')
    seconds_from_start: Optional[float] = Field(None, alias='secondsFromStart')
    duration: Optional[float] = None
    source: Optional[str] = None

    # Allow any other fields Vapi might send to prevent validation errors
    # for unexpected keys.
    model_config = {"extra": "allow"}

class OpenAIMessage(BaseModel):
    """Standard OpenAI message format (role, content, tool_calls, tool_call_id)."""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = Field(None, alias="toolCalls")
    tool_call_id: Optional[str] = Field(None, alias="toolCallId")
    name: Optional[str] = None # For tool role messages

    model_config = {"extra": "allow"}


class Artifact(BaseModel):
    messages: List[MessageEntry] # Uses our flexible MessageEntry
    messages_open_a_i_formatted: Optional[List[OpenAIMessage]] = Field(None, alias='messagesOpenAIFormatted')
    transcript: Optional[str] = None
    recording_url: Optional[HttpUrl] = Field(None, alias='recordingUrl') # Vapi sends this in end-of-call
    stereo_recording_url: Optional[HttpUrl] = Field(None, alias='stereoRecordingUrl') # Vapi sends this in end-of-call
    # Vapi's 'recording' object in 'end-of-call-report'
    recording: Optional[Dict[str, Any]] = None # Can be further typed if needed

    model_config = {"extra": "allow"}


class Character(BaseModel):
    age: Optional[int] = None # Made optional if not always present
    alias: Optional[str] = None
    birthplace: Optional[str] = None
    equipments: Optional[List[str]] = Field(default_factory=list)
    height: Optional[str] = None
    name: Optional[str] = None
    powers: Optional[List[str]] = Field(default_factory=list)
    super_skill: Optional[str] = Field(None, alias='superSkill')
    weakness: Optional[str] = None

    model_config = {"extra": "allow"}

class User(BaseModel):
    """
    Represents user data, often nested in metadata.
    Fields are made optional to handle cases where Vapi might not send all of them
    in every payload (e.g., webhook payloads vs. direct LLM call metadata).
    """
    username: Optional[str] = None # Made optional
    email: Optional[str] = None    # Made optional (key for webhook validation errors)
    id: Optional[str] = Field(None, alias='_id') # MongoDB ID, if present
    user_id: Optional[str] = None # Supabase UUID, if present
    character: Optional[Character] = Field(default_factory=Character)
    current_bg: Optional[str] = Field(None, alias='currentBg')
    notifications: Optional[List[Any]] = Field(default_factory=list)
    picture: Optional[HttpUrl] = None
    # Fields from Auth0 that might be in metadata:
    first_name: Optional[str] = Field(None, alias='firstName')
    last_name: Optional[str] = Field(None, alias='lastName')
    email_verified: Optional[bool] = Field(None, alias='emailVerified')
    account_status: Optional[str] = None
    signup_date: Optional[str] = None # Vapi sends as string

    model_config = {"extra": "allow"}


class UserDataWrapper(BaseModel):
    user: User

class Metadata(BaseModel):
    token: Optional[str] = None # Token might not always be in assistant default metadata
    data: Optional[UserDataWrapper] = None
    # Vapi also includes numAssistantTurns, numUserTurns in LLM request metadata
    num_assistant_turns: Optional[int] = Field(None, alias="numAssistantTurns")
    num_user_turns: Optional[int] = Field(None, alias="numUserTurns")

    model_config = {"extra": "allow"}

class FunctionProperty(BaseModel):
    description: Optional[str] = None
    type: str
    enum: Optional[List[str]] = None # For defaultQueryTool
    items: Optional[Dict[str, str]] = None # For array items type

class FunctionParameters(BaseModel):
    type: str = "object"
    properties: Dict[str, Union[FunctionProperty, str]] # str for cases like 'key':'****'
    required: Optional[List[str]] = None

class FunctionDefinition(BaseModel):
    name: str
    description: str
    parameters: FunctionParameters
    strict: Optional[bool] = None # For tools from Vapi
    async_: Optional[bool] = Field(None, alias="async") # For tools from Vapi

class ServerConfig(BaseModel):
    url: HttpUrl
    timeout_seconds: Optional[int] = Field(None, alias='timeoutSeconds')

class Tool(BaseModel): # For tools in assistant.model.tools
    id: str
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    type: str
    function: FunctionDefinition
    messages: Optional[List[Any]] = Field(default_factory=list) # Usually empty
    org_id: Optional[str] = Field(None, alias='orgId')
    server: Optional[ServerConfig] = None
    async_: Optional[bool] = Field(None, alias="async")

    model_config = {"extra": "allow"}

class Voice(BaseModel):
    model: Optional[str] = None
    voice_id: Optional[str] = Field(None, alias='voiceId')
    provider: Optional[str] = None
    input_min_characters: Optional[int] = Field(None, alias='inputMinCharacters')
    input_punctuation_boundaries: Optional[List[str]] = Field(None, alias='inputPunctuationBoundaries')

    model_config = {"extra": "allow"}

class KnowledgeBase(BaseModel):
    file_ids: Optional[List[str]] = Field(None, alias='fileIds')
    provider: Optional[str] = None

    model_config = {"extra": "allow"}

class Transcriber(BaseModel):
    model: Optional[str] = None
    language: Optional[str] = None
    numerals: Optional[bool] = None
    provider: Optional[str] = None
    confidence_threshold: Optional[float] = Field(None, alias='confidenceThreshold')

    model_config = {"extra": "allow"}

class AssistantModelConfig(BaseModel):
    url: Optional[HttpUrl] = None # Present in assistant.model but not assistantOverrides.model
    model: Optional[str] = None
    messages: Optional[List[OpenAIMessage]] = Field(default_factory=list) # System prompts
    provider: Optional[str] = None
    max_tokens: Optional[int] = Field(None, alias='maxTokens')
    temperature: Optional[float] = None
    functions: Optional[List[FunctionDefinition]] = Field(default_factory=list) # For direct functions
    tools: Optional[List[Tool]] = Field(default_factory=list) # For tools
    tool_ids: Optional[List[str]] = Field(None, alias='toolIds')
    knowledge_base: Optional[KnowledgeBase] = Field(None, alias='knowledgeBase')

    model_config = {"extra": "allow"}

class Monitor(BaseModel):
    listen_url: Optional[str] = Field(None, alias='listenUrl') # Allow wss://
    control_url: Optional[str] = Field(None, alias='controlUrl')

    model_config = {"extra": "allow"}

class Transport(BaseModel):
    provider: Optional[str] = None
    assistant_video_enabled: Optional[bool] = Field(None, alias='assistantVideoEnabled')
    call_url: Optional[HttpUrl] = Field(None, alias='callUrl') # Seen in end-of-call report

    model_config = {"extra": "allow"}

class AssistantOverrides(BaseModel):
    name: Optional[str] = None
    model: Optional[AssistantModelConfig] = None # This is the structure from Vapi for overrides
    first_message: Optional[str] = Field(None, alias='firstMessage')
    metadata: Optional[Metadata] = None # This contains your token and user data
    # Other overrides from Vapi end-of-call report
    transcriber: Optional[Transcriber] = None
    voice: Optional[Voice] = None

    model_config = {"extra": "allow"}

class Call(BaseModel):
    id: str
    org_id: Optional[str] = Field(None, alias='orgId')
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    type: Optional[str] = None
    monitor: Optional[Monitor] = None
    transport: Optional[Transport] = None
    web_call_url: Optional[HttpUrl] = Field(None, alias='webCallUrl')
    status: Optional[str] = None
    assistant_id: Optional[str] = Field(None, alias='assistantId')
    assistant_overrides: Optional[AssistantOverrides] = Field(None, alias='assistantOverrides')
    # Fields from end-of-call-report payload for 'call'
    started_at: Optional[str] = Field(None, alias="startedAt")
    ended_at: Optional[str] = Field(None, alias="endedAt")
    ended_reason: Optional[str] = Field(None, alias="endedReason")

    model_config = {"extra": "allow"}

class Assistant(BaseModel): # For the top-level 'assistant' object in Vapi webhooks
    id: Optional[str] = None
    org_id: Optional[str] = Field(None, alias='orgId')
    name: Optional[str] = None
    voice: Optional[Voice] = None
    created_at: Optional[str] = Field(None, alias='createdAt')
    updated_at: Optional[str] = Field(None, alias='updatedAt')
    model: Optional[AssistantModelConfig] = None
    recording_enabled: Optional[bool] = Field(None, alias='recordingEnabled')
    first_message: Optional[str] = Field(None, alias='firstMessage')
    end_call_function_enabled: Optional[bool] = Field(None, alias='endCallFunctionEnabled')
    transcriber: Optional[Transcriber] = None
    silence_timeout_seconds: Optional[int] = Field(None, alias='silenceTimeoutSeconds')
    client_messages: Optional[List[str]] = Field(None, alias='clientMessages')
    server_messages: Optional[List[str]] = Field(None, alias='serverMessages')
    dial_keypad_function_enabled: Optional[bool] = Field(None, alias='dialKeypadFunctionEnabled')
    hipaa_enabled: Optional[bool] = Field(None, alias='hipaaEnabled')
    max_duration_seconds: Optional[int] = Field(None, alias='maxDurationSeconds')
    metadata: Optional[Metadata] = None # Default assistant metadata
    voicemail_detection_enabled: Optional[bool] = Field(None, alias='voicemailDetectionEnabled')
    background_sound: Optional[str] = Field(None, alias='backgroundSound')
    backchanneling_enabled: Optional[bool] = Field(None, alias='backchannelingEnabled')
    background_denoising_enabled: Optional[bool] = Field(None, alias='backgroundDenoisingEnabled')
    message_plan: Optional[Dict[str, Any]] = Field(None, alias="messagePlan") # Seen in end-of-call
    server: Optional[ServerConfig] = None

    model_config = {"extra": "allow"}

# --- Analysis and Costing (from end-of-call report) ---
class AnalysisCostBreakdown(BaseModel):
    summary: Optional[float] = None
    summary_prompt_tokens: Optional[int] = Field(None, alias="summaryPromptTokens")
    summary_completion_tokens: Optional[int] = Field(None, alias="summaryCompletionTokens")
    structured_data: Optional[float] = Field(None, alias="structuredData")
    structured_data_prompt_tokens: Optional[int] = Field(None, alias="structuredDataPromptTokens")
    structured_data_completion_tokens: Optional[int] = Field(None, alias="structuredDataCompletionTokens")
    success_evaluation: Optional[float] = Field(None, alias="successEvaluation")
    success_evaluation_prompt_tokens: Optional[int] = Field(None, alias="successEvaluationPromptTokens")
    success_evaluation_completion_tokens: Optional[int] = Field(None, alias="successEvaluationCompletionTokens")
    model_config = {"extra": "allow"}

class CostBreakdown(BaseModel):
    stt: Optional[float] = None
    llm: Optional[float] = None
    tts: Optional[float] = None
    vapi: Optional[float] = None
    total: Optional[float] = None
    llm_prompt_tokens: Optional[int] = Field(None, alias="llmPromptTokens")
    llm_completion_tokens: Optional[int] = Field(None, alias="llmCompletionTokens")
    tts_characters: Optional[int] = Field(None, alias="ttsCharacters")
    voicemail_detection_cost: Optional[float] = Field(None, alias="voicemailDetectionCost")
    knowledge_base_cost: Optional[float] = Field(None, alias="knowledgeBaseCost")
    analysis_cost_breakdown: Optional[AnalysisCostBreakdown] = Field(None, alias="analysisCostBreakdown")
    model_config = {"extra": "allow"}

class CostEntry(BaseModel): # For the 'costs' array in end-of-call
    type: str
    cost: float
    transcriber: Optional[Dict[str, Any]] = None
    model: Optional[Dict[str, Any]] = None
    voice: Optional[Dict[str, Any]] = None
    minutes: Optional[float] = None
    sub_type: Optional[str] = Field(None, alias="subType")
    prompt_tokens: Optional[int] = Field(None, alias="promptTokens")
    completion_tokens: Optional[int] = Field(None, alias="completionTokens")
    characters: Optional[int] = None
    analysis_type: Optional[str] = Field(None, alias="analysisType")
    model_config = {"extra": "allow"}

class Analysis(BaseModel): # For end-of-call-report
    summary: Optional[str] = None
    success_evaluation: Optional[Union[str, bool]] = Field(None, alias="successEvaluation") # Can be "true" or boolean
    # Add other analysis fields if present
    model_config = {"extra": "allow"}


# ==============================================================================
# --- Top-Level ConversationUpdate Model (for Webhooks) ---
# ==============================================================================
class ConversationUpdate(BaseModel):
    """
    The root model representing the entire VAPI webhook event payload,
    specifically tailored for 'conversation-update' but flexible for others.
    """
    timestamp: int
    type: str # e.g., "conversation-update", "end-of-call-report", "speech-update"

    # --- Fields common in 'conversation-update' and 'model-output' (from LLM request to Vapi) ---
    # 'messages' from LLM request might be different from 'artifact.messages' in webhook
    messages: Optional[List[MessageEntry]] = Field(default_factory=list) # Present in 'conversation-update' & 'LLM request'
    conversation: Optional[List[MessageEntry]] = Field(default_factory=list) # Specifically in 'conversation-update'

    # --- Fields specific to 'model-output' from LLM ---
    output: Optional[Union[str, List[Dict[str, Any]]]] = None # Can be string or tool_calls list

    # --- Fields present in many webhook types ---
    artifact: Optional[Artifact] = None
    call: Optional[Call] = None
    assistant: Optional[Assistant] = None

    # --- Fields specific to 'end-of-call-report' ---
    analysis: Optional[Analysis] = None
    cost: Optional[float] = None # Top-level cost
    cost_breakdown: Optional[CostBreakdown] = Field(None, alias="costBreakdown")
    costs: Optional[List[CostEntry]] = None # Array of cost entries
    duration_ms: Optional[float] = Field(None, alias="durationMs") # Vapi often uses camelCase
    duration_seconds: Optional[float] = Field(None, alias="durationSeconds")
    duration_minutes: Optional[float] = Field(None, alias="durationMinutes")
    summary: Optional[str] = None # Top-level summary
    transcript: Optional[str] = None # Top-level transcript (different from artifact.transcript)
    # started_at, ended_at, ended_reason are under 'call' object for end-of-call

    # --- Fields for other event types (e.g., speech-update, status-update) ---
    status: Optional[str] = None # For 'status-update', 'speech-update'
    # For 'function-call'
    function_call: Optional[ToolCall] = Field(None, alias="functionCall")
    # For 'tool-calls' (if Vapi sends this event type distinctly)
    tool_calls: Optional[List[ToolCall]] = Field(None, alias="toolCalls")


    # Allow any other top-level fields Vapi might send for different event types
    model_config = {"extra": "allow"}