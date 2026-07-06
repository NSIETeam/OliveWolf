from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Avatar(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "avatars"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_type: Mapped[str] = mapped_column(String(40), nullable=False, default="portrait")
    source_asset_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_provider: Mapped[str] = mapped_column(String(40), nullable=False, default="elevenlabs")
    voice_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
