"""
数据库模型定义
使用SQLAlchemy ORM定义数据表结构
"""
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean, Integer, types # ADDED types
from sqlalchemy.orm import relationship, Mapped, mapped_column, declarative_base

Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    # preferences: Mapped[str] = mapped_column(Text, default="{}")  # 存储用户偏好设置的JSON字符串
    #todo: is_active 字段用于标识用户是否处于激活状态, 是否应该给DTOUser添加该字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # database 参数    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否被删除
    # 关系定义
    sessions = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    dialogues = relationship("DialogueRecord", back_populates="user")



    def __repr__(self):
        return f"<User {self.username}>"

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
    
  