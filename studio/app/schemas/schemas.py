from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TenantCreate(BaseModel):
    name: str
    slug: str
    plan: str = "studio"


class TenantRead(ORMModel):
    id: str
    name: str
    slug: str
    plan: str
    created_at: datetime


class ProjectCreate(BaseModel):
    tenant_id: str
    name: str
    description: str | None = None
    default_scene: str = "consultant"


class ProjectRead(ORMModel):
    id: str
    tenant_id: str
    name: str
    description: str | None
    default_scene: str
    created_at: datetime


class AvatarCreate(BaseModel):
    tenant_id: str
    project_id: str
    name: str
    avatar_type: str = "portrait"
    voice_provider: str = "elevenlabs"
    voice_id: str | None = None


class AvatarRead(ORMModel):
    id: str
    tenant_id: str
    project_id: str
    name: str
    avatar_type: str
    source_asset_uri: str | None
    voice_provider: str
    voice_id: str | None
    status: str
    created_at: datetime


class KnowledgeSourceCreate(BaseModel):
    tenant_id: str
    project_id: str
    name: str
    source_type: str = "text"
    content_uri: str | None = None


class KnowledgeSourceRead(ORMModel):
    id: str
    tenant_id: str
    project_id: str
    name: str
    source_type: str
    content_uri: str | None
    status: str
    created_at: datetime


class RenderJobCreate(BaseModel):
    tenant_id: str
    project_id: str
    avatar_id: str
    job_type: str = "talking_video"
    scene: str = "consultant"
    input_text: str | None = None


class RenderJobRead(ORMModel):
    id: str
    tenant_id: str
    project_id: str
    avatar_id: str
    job_type: str
    scene: str
    input_text: str | None
    status: str
    output_uri: str | None
    error_message: str | None
    created_at: datetime


class TrainingJobCreate(BaseModel):
    tenant_id: str
    project_id: str
    avatar_id: str
    job_type: str = "avatar_build"
    training_preset: str = "portrait_realtime"


class TrainingJobRead(ORMModel):
    id: str
    tenant_id: str
    project_id: str
    avatar_id: str
    job_type: str
    training_preset: str
    status: str
    progress: str
    output_uri: str | None
    error_message: str | None
    created_at: datetime


class ConversationTestRequest(BaseModel):
    tenant_id: str
    project_id: str
    avatar_id: str | None = None
    scene: str = "consultant"
    message: str


class ConversationTestResponse(BaseModel):
    answer: str
    mode: str = "mock"
