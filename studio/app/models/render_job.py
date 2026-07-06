from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class RenderJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "render_jobs"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    avatar_id: Mapped[str] = mapped_column(String(36), ForeignKey("avatars.id"), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(40), nullable=False, default="talking_video")
    scene: Mapped[str] = mapped_column(String(80), nullable=False, default="consultant")
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued")
    output_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
