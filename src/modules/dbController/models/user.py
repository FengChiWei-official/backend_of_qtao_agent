from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import declarative_base

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
