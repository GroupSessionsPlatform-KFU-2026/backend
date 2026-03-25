from typing import Optional, Sequence
from uuid import UUID

from src.app.dependencies.repositories import (
    RoomParticipantRepository,
    RoomParticipantRepositoryDep,
)
from src.app.models.room_participant import (
    RoomParticipant,
    RoomParticipantUpdate,
)
from src.app.schemas.room_participant_filters import ParticipantFilters


class RoomParticipantService:
    __repository: RoomParticipantRepository

    def __init__(self, repository: RoomParticipantRepositoryDep):
        self.__repository = repository

    async def get_participants(
        self, filters: ParticipantFilters
    ) -> Sequence[RoomParticipant]:
        return await self.__repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def update_participant(
        self, participant_update: RoomParticipantUpdate, participant_id: UUID
    ) -> Optional[RoomParticipant]:
        return await self.__repository.update(
            participant_id, participant_update
        )

    async def delete_participant(
        self, participant_id: UUID
    ) -> Optional[RoomParticipant]:
        return await self.__repository.delete(participant_id)