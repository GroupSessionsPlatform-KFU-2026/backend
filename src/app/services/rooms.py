import secrets
import string
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    RoomParticipantRepository,
    RoomParticipantRepositoryDep,
    RoomRepository,
    RoomRepositoryDep,
)
from src.app.models.room import Room, RoomCreate, RoomUpdate
from src.app.models.room_participant import RoomParticipant
from src.app.routers.rooms import JoinRoomRequest
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest


def generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class RoomService:
    __room_repository: RoomRepository
    __room_participant_repository: RoomParticipantRepository

    def __init__(
        self,
        room_repository: RoomRepositoryDep,
        room_participant_repository: RoomParticipantRepositoryDep,
    ):
        self.__room_repository = room_repository
        self.__room_participant_repository = room_participant_repository

    async def get_rooms(self, filters: RoomFilters) -> Sequence[Room]:
        return await self.__room_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    # We should change when will have auth
    async def create_room(self, room_create: RoomCreate) -> Room:
        room_dump = room_create.model_dump()
        room = Room(
            **room_dump,
            room_code=generate_room_code(),
            status='active',
        )
        return await self.__room_repository.save(room)

    async def get_room(self, room_id: UUID) -> Optional[Room]:
        return await self.__room_repository.get(room_id)

    async def update_room(
        self, room_update: RoomUpdate, room_id: UUID
    ) -> Optional[Room]:
        return await self.__room_repository.update(room_id, room_update)

    async def end_room(self, room_id: UUID) -> Optional[Room]:
        room = await self.__room_repository.get(room_id)
        if room is None:
            return None
        room.status = 'ended'
        return await self.__room_repository.save(room)

    # We must change when will be auth
    async def join_room(self, payload: JoinRoomRequest) -> Optional[RoomParticipant]:
        filters = RoomFilters(room_code=payload.room_code, offset=0, limit=1)
        rooms = await self.__room_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

        if not rooms:
            return None

        room = rooms[0]

        participant = RoomParticipant(
            room_id=room.id,
            user_id=payload.user_id,
            role='participant',
            is_kicked=False,
        )
        return await self.__room_participant_repository.save(participant)
