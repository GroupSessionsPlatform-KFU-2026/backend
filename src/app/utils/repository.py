from typing import Any, Optional, Sequence
from uuid import UUID

from generics import get_filled_type
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.app.dependencies.session import SessionDep
from src.app.models.base import BaseModel

type FilterType = _ColumnExpressionArgument[bool] | bool
type PkType = int | UUID


class Repository[Model: BaseModel]:
    __model: type[Model] | None = None
    __session: AsyncSession

    @property
    def model(self) -> type[Model]:
        if self.__model is None:
            self.__model = get_filled_type(self, Repository, 0)
        return self.__model

    def __init__(self, session: SessionDep):
        self.__session = session

    async def get(self, pk: PkType) -> Optional[Model]:
        return await self.__session.get(self.model, pk)

    async def fetch(
        self,
        filters: Optional[PydanticBaseModel] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> Sequence[Model]:
        select_statement = select(self.model)
        filter_statement = and_(True)

        filters_dict: dict[str, Any] = {}
        if filters is not None:
            filters_dict.update(filters.model_dump(exclude_unset=True))

        if extra_filters is not None:
            filters_dict.update(extra_filters)

        for key, value in filters_dict.items():
            if key in {'offset', 'limit'}:
                continue
            if not hasattr(self.model, key):
                continue
            if value is not None:
                filter_statement = and_(
                    filter_statement,
                    getattr(self.model, key) == value,
                )

        select_statement = select_statement.where(filter_statement)

        if offset is not None:
            select_statement = select_statement.offset(offset)

        if limit is not None:
            select_statement = select_statement.limit(limit)

        entities = await self.__session.exec(select_statement)
        return entities.all()


    async def get_one_by_filters(
        self,
        filters: Optional[PydanticBaseModel] = None,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> Optional[Model]:
        entities = await self.fetch(
            filters=filters,
            limit=1,
            extra_filters=extra_filters,
        )
        if not entities:
            return None
        return entities[0]

    async def exists_by_filters(
        self,
        filters: Optional[PydanticBaseModel] = None,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> bool:
        return (
            await self.get_one_by_filters(
                filters=filters,
                extra_filters=extra_filters,
            )
            is not None
        )

    async def save(self, instance: Model) -> Model:
        self.__session.add(instance)
        await self.__session.commit()
        await self.__session.refresh(instance)
        return instance

    async def save_all(self, instances: list[Model]) -> list[Model]:
        self.__session.add_all(instances)
        await self.__session.commit()

        for instance in instances:
            await self.__session.refresh(instance)

        return instances

    async def delete(self, pk: PkType) -> Optional[Model]:
        instance = await self.get(pk)
        if instance is None:
            return None

        await self.__session.delete(instance)
        await self.__session.commit()
        return instance

    async def update(
        self,
        pk: PkType,
        updates: PydanticBaseModel,
    ) -> Optional[Model]:
        instance = await self.get(pk)
        if instance is None:
            return None

        instance_update_dump = updates.model_dump(exclude_unset=True)

        for key, value in instance_update_dump.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.save(instance)
        return instance
    
    async def count(
        self,
        filters: Optional[PydanticBaseModel] = None,
        extra_filters: Optional[dict[str, Any]] = None,
    ) -> int:
        return len(
            await self.fetch(
                filters=filters,
                extra_filters=extra_filters,
            )
        )
