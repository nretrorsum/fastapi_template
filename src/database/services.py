from datetime import UTC, datetime
from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import DateTime, MetaData, Uuid, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    DeclarativeBase,
    InstrumentedAttribute,
    Mapped,
    mapped_column,
    selectinload,
)

T = TypeVar("T")


def utcnow_naive():
    return datetime.now(UTC).replace(tzinfo=None)

class Base(DeclarativeBase):
    metadata = MetaData()


class CoreModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow_naive,
        onupdate=utcnow_naive
    )

    @classmethod
    def _get_query(
            cls,
            prefetch: tuple[str, ...] | None = None,
            options: list[Any] | None = None,
            filters: Any | None = None,
    ) -> Any:
        query = select(cls)

        if prefetch:
            if not options:
                options = []
            options.extend(selectinload(getattr(cls, x)) for x in prefetch)
            query = query.options(*options).execution_options(populate_existing=True)

        if options:
            query = query.options(*options)

        if filters:
            query = filters.filter(query)
            query = filters.sort(query)

        return query

    @classmethod
    async def all(
            cls,
            session: AsyncSession,
            prefetch: tuple[str, ...] | None = None,
            filters: Any | None = None,
            options: list[Any] | None = None,
            sort_by_creation: bool | None = None,
    ) -> list[Any]:
        query = cls._get_query(prefetch, options, filters)
        if sort_by_creation:
            query = query.order_by(cls.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_field(
            cls,
            session: AsyncSession,
            field_name: str,
            value: Any,
            prefetch: tuple[str, ...] | None = None,
            options: list[Any] | None = None,
    ) -> Any:
        field = getattr(cls, field_name)
        if not field:
            raise AttributeError(f"Field {field_name} is not defined")

        query = select(cls).where(field == value)

        if prefetch:
            if not options:
                options = []
            options.extend(selectinload(getattr(cls, rel)) for rel in prefetch)
            query = query.options(*options).execution_options(populate_existing=True)
        elif options:
            query = query.options(*options)

        result = await session.execute(query)
        obj = result.scalar_one_or_none()
        if obj:
            await session.refresh(obj)
        return obj

    @classmethod
    async def create(
            cls,
            data: T | BaseModel | dict,
            session: AsyncSession,
    ) -> T:
        if not isinstance(data, cls):
            if isinstance(data, BaseModel):
                data = data.model_dump(exclude_unset=True)
            if isinstance(data, dict):
                data = cls(**data)

        session.add(data)
        await session.commit()
        await session.refresh(data)
        return data

    @classmethod
    async def update(
            cls,
            session: AsyncSession,
            data_to_change: dict[str, Any],
            where_clause=None
    ):
        for field in data_to_change.keys():
            attr = getattr(cls, field, None)
            if attr is None or not isinstance(attr, InstrumentedAttribute):
                raise AttributeError(f"No column '{field}' on {cls.__name__}")

        stmt = update(cls).values(data_to_change)

        if where_clause is not None:
            stmt = stmt.where(where_clause)
        stmt = stmt.returning(cls)

        result = await session.execute(stmt)
        await session.commit()
        data = result.scalars().all()

        if len(data) > 1:
            return data
        return data[0] if data else None

    @classmethod
    async def delete(
            cls,
            session: AsyncSession,
            where_clause: Any | None = None,
            *,
            returning: bool = False,
            allow_all: bool = False,
    ) -> Any:
        if where_clause is None and not allow_all:
            raise ValueError(
                "Deleting all rows are denied, try to use allow_all=True parameter"
            )

        stmt = delete(cls)

        if where_clause is not None:
            stmt = stmt.where(where_clause)

        if returning:
            stmt = stmt.returning(cls)

        result = await session.execute(stmt)
        await session.commit()

        if returning:
            return result.scalars().all()

        return result.rowcount

