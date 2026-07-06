from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class KnowledgeSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "knowledge_sources"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="text")
    content_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
