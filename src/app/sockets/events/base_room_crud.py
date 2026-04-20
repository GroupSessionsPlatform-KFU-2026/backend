from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

import socketio

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


def _error_response(message: str) -> dict[str, Any]:
    return {
        'ok': False,
        'error': message,
    }


class BaseRoomCrudSocketHandler[ServiceT, CreateSchemaT, UpdateSchemaT](ABC):
    _create_command: str
    _update_command: str
    _delete_command: str

    _write_scope: str
    _delete_scope: str

    _created_event: str
    _updated_event: str
    _deleted_event: str

    _resource_response_key: str
    _deleted_response_key: str

    _create_target_not_found_message: str
    _resource_not_found_message: str
    _update_forbidden_message: str
    _delete_forbidden_message: str

    def __init__(
        self,
        *,
        socket_manager: SocketConnectionManager,
        context_factory: Any,
        error_cls: type[Exception],
    ) -> None:
        self._socket_manager = socket_manager
        self._context_factory = context_factory
        self._error_cls = error_cls

    def register(self, sio: socketio.AsyncServer) -> None:
        @sio.on(self._create_command)
        async def _on_create(sid: str, data: dict | None):
            try:
                return await self._handle_create(sid, data)
            except self._error_cls as error:
                return _error_response(str(error))

        @sio.on(self._update_command)
        async def _on_update(sid: str, data: dict | None):
            try:
                return await self._handle_update(sid, data)
            except self._error_cls as error:
                return _error_response(str(error))

        @sio.on(self._delete_command)
        async def _on_delete(sid: str, data: dict | None):
            try:
                return await self._handle_delete(sid, data)
            except self._error_cls as error:
                return _error_response(str(error))

    async def _handle_create(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self._error_cls)
        identity = await require_identity(self._socket_manager, sid, self._error_cls)
        require_scope(identity, self._write_scope, self._error_cls)

        create_payload = self._parse_create_payload(payload, identity)

        async with self._context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self._error_cls,
            )
            created_resource = await self._create_resource(
                service,
                identity,
                create_payload,
            )
            if created_resource is None:
                raise self._error_cls(self._create_target_not_found_message)

        resource_payload = created_resource.model_dump(mode='json')

        await self._socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self._created_event,
            data=resource_payload,
        )

        return ok_response(**{self._resource_response_key: resource_payload})

    async def _handle_update(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self._error_cls)
        identity = await require_identity(self._socket_manager, sid, self._error_cls)
        require_scope(identity, self._write_scope, self._error_cls)

        resource_ids, update_payload = self._parse_update_payload(payload)

        async with self._context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self._error_cls,
            )

            existing_resource = await self._get_existing_resource(
                service,
                identity,
                resource_ids,
            )
            if existing_resource is None:
                raise self._error_cls(self._resource_not_found_message)

            ensure_can_manage_resource(
                author_id=self._get_author_id(existing_resource),
                identity=identity,
                message=self._update_forbidden_message,
                error_cls=self._error_cls,
            )

            updated_resource = await self._update_resource(
                service,
                identity,
                resource_ids,
                update_payload,
            )
            if updated_resource is None:
                raise self._error_cls(self._resource_not_found_message)

        resource_payload = updated_resource.model_dump(mode='json')

        await self._socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self._updated_event,
            data=resource_payload,
        )

        return ok_response(**{self._resource_response_key: resource_payload})

    async def _handle_delete(
        self,
        sid: str,
        data: dict | None,
    ) -> dict[str, Any]:
        payload = require_payload_dict(data, self._error_cls)
        identity = await require_identity(self._socket_manager, sid, self._error_cls)
        require_scope(identity, self._delete_scope, self._error_cls)

        resource_ids = self._parse_delete_payload(payload)

        async with self._context_factory() as (room_repository, service):
            await ensure_room_is_active(
                room_repository,
                identity.room_id,
                self._error_cls,
            )

            existing_resource = await self._get_existing_resource(
                service,
                identity,
                resource_ids,
            )
            if existing_resource is None:
                raise self._error_cls(self._resource_not_found_message)

            ensure_can_manage_resource(
                author_id=self._get_author_id(existing_resource),
                identity=identity,
                message=self._delete_forbidden_message,
                error_cls=self._error_cls,
            )

            deleted_resource = await self._delete_resource(
                service,
                identity,
                resource_ids,
            )
            if deleted_resource is None:
                raise self._error_cls(self._resource_not_found_message)

        deleted_payload = self._build_deleted_event_payload(identity, resource_ids)

        await self._socket_manager.emit_to_room(
            room_id=identity.room_id,
            event=self._deleted_event,
            data=deleted_payload,
        )

        deleted_id = self._get_deleted_id(resource_ids)

        return ok_response(**{self._deleted_response_key: str(deleted_id)})

    @abstractmethod
    def _parse_create_payload(
        self,
        payload: dict[str, Any],
        identity: SocketIdentity,
    ) -> CreateSchemaT: ...

    @abstractmethod
    def _parse_update_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, UUID], UpdateSchemaT]: ...

    @abstractmethod
    def _parse_delete_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, UUID]: ...

    @abstractmethod
    async def _create_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        payload: CreateSchemaT,
    ) -> Any | None: ...

    @abstractmethod
    async def _get_existing_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> Any | None: ...

    @abstractmethod
    async def _update_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
        payload: UpdateSchemaT,
    ) -> Any | None: ...

    @abstractmethod
    async def _delete_resource(
        self,
        service: ServiceT,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> Any | None: ...

    @abstractmethod
    def _get_author_id(self, resource: Any) -> UUID: ...

    @abstractmethod
    def _build_deleted_event_payload(
        self,
        identity: SocketIdentity,
        resource_ids: dict[str, UUID],
    ) -> dict[str, Any]: ...

    @abstractmethod
    def _get_deleted_id(self, resource_ids: dict[str, UUID]) -> UUID: ...
