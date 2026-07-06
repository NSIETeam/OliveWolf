from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class TrainingJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "training_jobs"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    avatar_id: Mapped[str] = mapped_column(String(36), ForeignKey("avatars.id"), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(60), nullable=False, default="avatar_build")
    training_preset: Mapped[str] = mapped_column(String(80), nullable=False, default="portrait_realtime")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued")
    progress: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    output_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
