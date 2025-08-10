from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, InstrumentedAttribute
from typing import Optional, Tuple, List, Dict, Any, Type
import logging
from src.database.connection import async_session

from src.database.connection import get_db

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    metadata = MetaData()


class CoreModel(Base):
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def _get_query(
            cls,
            prefetch: Optional[Tuple[str, ...]] = None,
            options: Optional[List[Any]] = None,
            filters: Optional[Any] = None,
    ) -> Any:
        query = select(cls)
        print(f'Class used:{cls.__name__}')
        print(f'V1 of query: {query}')
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
            prefetch: Optional[Tuple[str, ...]] = None,
            filters: Optional[Any] = None,
            options: Optional[List[Any]] = None,
            sort_by_creation: Optional[bool] = None,
    ) -> List[Any]:

        async with async_session() as session:
            query = cls._get_query(prefetch, options, filters)
            if sort_by_creation:
                query = query.order_by(cls.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_by_field(
            cls,
            field_name: str,
            value: str,
            prefetch: Optional[Tuple[str, ...]] = None,
            options: Optional[List[Any]] = None,
    ) -> Any:

        field = getattr(cls, field_name)
        if not field:
            raise AttributeError(f'Field {field_name} is not defined')
        query = select(cls).where(field == value)
        print(query)

        if prefetch:
            if not options:
                options = []
            options.extend(selectinload(getattr(cls, rel)) for rel in prefetch)
            query = query.options(*options).execution_options(populate_existing=True)

        elif options:
            query = query.options(*options)

        async with async_session() as session:
            result = await session.execute(query)
            obj = result.scalar_one_or_none()

        return obj

    @classmethod
    async def create(
            cls,
            creation_model,
        ):
        async with async_session() as session:
            session.add(creation_model)
            await session.commit()
            await session.refresh(creation_model)
            return creation_model

    @classmethod
    async def update(
            cls,
            data_to_change: Dict[str, Any],
            where_clause=None
    ):
        for field in data_to_change.keys():
            attr = getattr(cls, field, None)
            if attr is None or not isinstance(attr, InstrumentedAttribute):
                raise AttributeError(f"No column '{field_to_change}' on {cls.__name__}")

        stmt = update(cls).values(data_to_change)

        if where_clause is not None:
            stmt = stmt.where(where_clause)
        stmt = stmt.returning(cls)

        async with async_session() as session:
            result = await session.execute(stmt)
            await session.commit()
            data = result.scalars().all()
            if len(data)>1:
                return data
            return data[0]

    @classmethod
    async def delete(
            cls,
            where_clause: Optional[Any] = None,
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
            if isinstance(where_clause, Sequence) and not isinstance(where_clause, str):
                for condition in where_clause:
                    stmt = stmt.where(condition)
            else:
                stmt = stmt.where(where_clause)

        if returning:
            stmt = stmt.returning(cls)

        async with async_session as session:
            result = await session.execute(stmt)

        if returning:
            return result.scalars().all()
        return result.rowcount