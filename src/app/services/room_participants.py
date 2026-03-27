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
        repository_filters = RoomParticipantFilters(
            user_id=filters.user_id,
            role=filters.role,
            is_kicked=filters.is_kicked,
            offset=filters.offset,
            limit=filters.limit,
        )
        participants = await self.__repository.fetch(
            filters=repository_filters,
            offset=repository_filters.offset,
            limit=repository_filters.limit,
        )
        return [
            participant
            for participant in participants
            if participant.room_id == room_id
        ]

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
        filters = RoomParticipantFilters(
            user_id=user_id,
            offset=0,
            limit=100,
        )
        participants = await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

        for participant in participants:
            if participant.room_id == room_id:
                return participant
        return None

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
