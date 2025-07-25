import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, ForeignKey, Text, Boolean, DateTime, types
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class JsonEncodedList(types.TypeDecorator):
    """自定义类型，用于存储JSON编码的列表"""
    impl = Text

    def process_bind_param(self, value: Optional[List[str]], dialect) -> Optional[str]:
        if value is None or value == []:
            return '[]'
        return json.dumps(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[List[str]]:
        if value is None or value == '[]':
            return []
        return json.loads(value)


class DialogueRecord(Base):
    """对话记录表"""
    __tablename__ = "dialogue_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    system_response: Mapped[str] = mapped_column(Text, nullable=False)
    system_thoughts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_list: Mapped[Optional[List[str]]] = mapped_column(JsonEncodedList, nullable=True, default=list)  # Remove server_default to avoid MySQL TEXT default issue
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否已被审阅

    # Making query_sent_at optional with default value to match existing database schema
    query_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    response_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # 关系定义
    session = relationship("Conversation", back_populates="records")
    user = relationship("User", back_populates="dialogues")


    def __repr__(self):
        return f"<DialogueRecord {self.id[:8]}>"


