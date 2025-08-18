from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DECIMAL, JSON, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.services import CoreModel


class User(CoreModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    user_gender: Mapped[str] = mapped_column(String, nullable=True)
    user_birthday: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    user_preferences: Mapped[dict] = mapped_column(JSON, nullable=True)
    user_avatar: Mapped[str] = mapped_column(String, nullable=True)
    user_weight: Mapped[Decimal] = mapped_column(DECIMAL, nullable=True)
    user_height: Mapped[Decimal] = mapped_column(DECIMAL, nullable=True)
    user_subscription: Mapped[str] = mapped_column(String, nullable=True)
    blacked_refresh_tokens: Mapped[list["BlackedRefreshTokens"]] = relationship(
        "BlackedRefreshTokens",
        back_populates="user",
        cascade="all, delete-orphan",
        single_parent=True,
    )

    refresh_tokens: Mapped[list["UserRefreshTokens"]] = relationship(
        "UserRefreshTokens",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class BlackedRefreshTokens(CoreModel):
    __tablename__ = "blacked_refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="blacked_refresh_tokens",
    )


class UserRefreshTokens(CoreModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    user: Mapped[User] = relationship(
        "User",
        back_populates="refresh_tokens",
    )
