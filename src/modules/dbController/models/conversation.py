import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_name: Mapped[Optional[str]] = mapped_column(String(100))

    # dbase 参数
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否被删除
    # 关系定义
    user = relationship("User", back_populates="sessions")
    records = relationship("DialogueRecord", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<conversations {self.session_name}>"
