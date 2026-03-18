from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    RoomParticipantRepository,
    RoomParticipantRepositoryDep,
)
from src.app.models.room_participant import (
    RoomParticipant,
    RoomParticipantCreate,
    RoomParticipantUpdate,
)
from src.app.schemas.room_participant_filters import RoomParticipantFilters


class RoomParticipantService:
    __repository: RoomParticipantRepository

    def __init__(self, repository: RoomParticipantRepositoryDep):
        self.__repository = repository

    async def get_participants(
        self,
        room_id: UUID,
        filters: RoomParticipantFilters,
    ) -> Sequence[RoomParticipant]:
        return await self.__repository.fetch(
            filters=filters,
            extra_filters={'room_id': room_id},
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_participant(
        self,
        participant_create: RoomParticipantCreate,
    ) -> RoomParticipant:
        participant_dump = participant_create.model_dump()
        participant = RoomParticipant(
            **participant_dump,
            role='participant',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        )
        return await self.__repository.save(participant)

    async def get_participant_in_room(
        self,
        room_id: UUID,
        user_id: UUID,
    ) -> Optional[RoomParticipant]:
        participants = await self.__repository.fetch(
            extra_filters={
                'room_id': room_id,
                'user_id': user_id,
            },
            limit=1,
        )
        return participants[0] if participants else None

    async def update_participant(
        self,
        room_id: UUID,
        user_id: UUID,
        participant_update: RoomParticipantUpdate,
    ) -> Optional[RoomParticipant]:
        participant = await self.get_participant_in_room(room_id, user_id)
        if participant is None:
            return None
        return await self.__repository.update(participant.id, participant_update)

    async def remove_participant(
        self,
        room_id: UUID,
        user_id: UUID,
    ) -> Optional[RoomParticipant]:
        participant = await self.get_participant_in_room(room_id, user_id)
        if participant is None:
            return None

        participant.left_at = datetime.now(timezone.utc)
        return await self.__repository.save(participant)
    
    async def count_participants(
        self,
        room_id: UUID,
        filters: RoomParticipantFilters,
    ) -> int:
        return await self.__repository.count(
            filters=filters,
            extra_filters={'room_id': room_id},
        )
