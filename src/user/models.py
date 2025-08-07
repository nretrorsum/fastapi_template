from uuid import UUID, uuid4
from sqlalchemy import String, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.services import CoreModel

class User(CoreModel):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    blacked_refresh_tokens: Mapped[list["BlackedRefreshTokens"]] = relationship(
        "BlackedRefreshTokens",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    refresh_tokens: Mapped["UserRefreshTokens"] = relationship(
        "UserRefreshTokens",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class BlackedRefreshTokens(CoreModel):
    __tablename__ = 'blacked_refresh_tokens'

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('users.id'), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="blacked_refresh_tokens")

class UserRefreshTokens(CoreModel):

    __tablename__ = 'refresh_tokens'

    user_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey('users.id'), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    user: Mapped[User] = relationship(
        "User",
        back_populates="refresh_tokens",
        uselist=False,
    )