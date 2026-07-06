from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Project(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "projects"

    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_scene: Mapped[str] = mapped_column(String(80), nullable=False, default="consultant")
