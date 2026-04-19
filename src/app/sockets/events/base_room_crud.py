from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.app.sockets.events.common import (
    SocketIdentity,
    ensure_can_manage_resource,
    ensure_room_is_active,
    ok_response,
    require_identity,
    require_payload_dict,
    require_scope,
)
from src.app.sockets.manager import SocketConnectionManager


class BaseRoomCrudSocketHandler[ServiceT, CreateSchemaT, UpdateSchemaT](ABC):
    write_scope: str
    delete_scope: str

    created_event: str
    updated_event: str
    deleted_event: str

    resource_response_key: str
    deleted_response_key: str

    create_target_not_found_message: str
    resource_not_found_message: str
    update_forbidden_message: str
    delete_forbidden_message: str

    def __init__(
        self,
        *,
        socket_manager: SocketConnectionManager,
        context_factory: Any,
        error_cls: type[Exception],
    ) -> None:
        self.socket_manager = socket_manager
        self.context_factory = context_factory
        self.error_cls = error_cls

    async def handle_create(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self.error_cls)
        identity = await require_identity(self.socket_manager, sid, self.error_cls)
        require_scope(identity, self.write_scope, self.error_cls)

        create_payload = self.parse_create_payload(payload, identity)

        async with self.context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self.error_cls,
            )
            created_resource = await self.create_resource(
                service,
                identity,
                create_payload,
            )
            if created_resource is None:
                raise self.error_cls(self.create_target_not_found_message)

        resource_payload = created_resource.model_dump(mode='json')

        await self.socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self.created_event,
            data=resource_payload,
        )

        return ok_response(**{self.resource_response_key: resource_payload})

    async def handle_update(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self.error_cls)
        identity = await require_identity(self.socket_manager, sid, self.error_cls)
        require_scope(identity, self.write_scope, self.error_cls)

        resource_ids, update_payload = self.parse_update_payload(payload)

        async with self.context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self.error_cls,
            )

            existing_resource = await self.get_existing_resource(
                service,
                identity,
                resource_ids,
            )
            if existing_resource is None:
                raise self.error_cls(self.resource_not_found_message)

            ensure_can_manage_resource(
                author_id=self.get_author_id(existing_resource),
                identity=identity,
                message=self.update_forbidden_message,
                error_cls=self.error_cls,
            )

            updated_resource = await self.update_resource(
                service,
                identity,
                resource_ids,
                update_payload,
            )
            if updated_resource is None:
                raise self.error_cls(self.resource_not_found_message)

        resource_payload = updated_resource.model_dump(mode='json')

        await self.socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self.updated_event,
            data=resource_payload,
        )

        return ok_response(**{self.resource_response_key: resource_payload})

    async def handle_delete(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self.error_cls)
        identity = await require_identity(self.socket_manager, sid, self.error_cls)
        require_scope(identity, self.delete_scope, self.error_cls)

        resource_ids = self.parse_delete_payload(payload)

        async with self.context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self.error_cls,
            )

            existing_resource = await self.get_existing_resource(
                service,
                identity,
                resource_ids,
            )
            if existing_resource is None:
                raise self.error_cls(self.resource_not_found_message)

            ensure_can_manage_resource(
                author_id=self.get_author_id(existing_resource),
                identity=identity,
                message=self.delete_forbidden_message,
                error_cls=self.error_cls,
            )

            deleted_resource = await self.delete_resource(
                service,
                identity,
                resource_ids,
            )
            if deleted_resource is None:
                raise self.error_cls(self.resource_not_found_message)

        deleted_payload = self.build_deleted_event_payload(identity, resource_ids)

        await self.socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self.deleted_event,
            data=deleted_payload,
        )

        deleted_id = self.get_deleted_id(resource_ids)

        return ok_response(**{self.deleted_response_key: str(deleted_id)})

    @abstractmethod
    def parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> CreateSchemaT: ...

    @abstractmethod
    def parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], UpdateSchemaT]: ...

    @abstractmethod
    def parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]: ...

    @abstractmethod
    async def create_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        payload: CreateSchemaT,
    ) -> Any | None: ...

    @abstractmethod
    async def get_existing_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> Any | None: ...

    @abstractmethod
    async def update_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: UpdateSchemaT,
    ) -> Any | None: ...

    @abstractmethod
    async def delete_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> Any | None: ...

    @abstractmethod
    def get_author_id(self, resource: Any) -> UUID: ...

    @abstractmethod
    def build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]: ...

    @abstractmethod
    def get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID: ...
