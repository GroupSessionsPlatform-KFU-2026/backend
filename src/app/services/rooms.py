import secrets
import string
from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from fastapi import HTTPException, status

from src.app.dependencies.repositories import (
    PomodoroSessionRepository,
    PomodoroSessionRepositoryDep,
    RoomParticipantRepository,
    RoomParticipantRepositoryDep,
    RoomRepository,
    RoomRepositoryDep,
)
from src.app.models.pomodoro_session import PomodoroPhase, PomodoroSession
from src.app.models.room import Room, RoomCreate, RoomStatus, RoomUpdate
from src.app.models.room_participant import RoomParticipant
from src.app.schemas.room_filters import RoomFilters
from src.app.schemas.room_request import JoinRoomRequest


def generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class RoomService:
    __room_repository: RoomRepository
    __room_participant_repository: RoomParticipantRepository
    __pomodoro_repository: PomodoroSessionRepository

    def __init__(
        self,
        room_repository: RoomRepositoryDep,
        room_participant_repository: RoomParticipantRepositoryDep,
        pomodoro_repository: PomodoroSessionRepositoryDep,
    ):
        self.__room_repository = room_repository
        self.__room_participant_repository = room_participant_repository
        self.__pomodoro_repository = pomodoro_repository

    async def get_rooms(self, filters: RoomFilters) -> Sequence[Room]:
        return await self.__room_repository.fetch(
            filters=filters,
            offset=filters.offset,
            limit=filters.limit,
        )

    async def create_room(self, room_create: RoomCreate, creator_id: UUID) -> Room:
        room_dump = room_create.model_dump(exclude={'creator_id'})

        room = Room(
            **room_dump,
            creator_id=creator_id,
            room_code=generate_room_code(),
            status=RoomStatus.ACTIVE,
            ended_at=None,
        )

        saved_room = await self.__room_repository.save(room)

        pomodoro = PomodoroSession(
            room_id=saved_room.id,
            work_duration=25,
            short_break_duration=5,
            long_break_duration=15,
            cycles_before_long=4,
            current_phase=PomodoroPhase.WORK,
            completed_cycles=0,
            is_running=False,
            phase_ends_at=None,
            session_ends_at=None,
        )
        await self.__pomodoro_repository.save(pomodoro)

        return saved_room

    async def get_room(self, room_id: UUID) -> Optional[Room]:
        return await self.__room_repository.get(room_id)

    async def update_room(
        self,
        room_update: RoomUpdate,
        room_id: UUID,
        actor_id: UUID,
    ) -> Optional[Room]:
        room = await self.__room_repository.get(room_id)
        if room is None:
            return None

        if room.creator_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only room creator can update room',
            )

        update_dump = room_update.model_dump(exclude_unset=True)
        for key, value in update_dump.items():
            setattr(room, key, value)

        return await self.__room_repository.save(room)

    async def end_room(self, room_id: UUID, actor_id: UUID) -> Optional[Room]:
        room = await self.__room_repository.get(room_id)
        if room is None:
            return None

        if room.creator_id != actor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only room creator can end room',
            )

        room.status = RoomStatus.ENDED
        room.ended_at = datetime.now(timezone.utc)
        return await self.__room_repository.save(room)

    async def join_room(
        self,
        payload: JoinRoomRequest,
        user_id: UUID,
    ) -> Optional[RoomParticipant]:
        room = await self.__room_repository.get_one_by_filters(
            extra_filters={'room_code': payload.room_code},
        )
        if room is None:
            return None

        if room.status == RoomStatus.ENDED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Cannot join an ended room',
            )

        existing_participant = (
            await self.__room_participant_repository.get_one_by_filters(
                extra_filters={
                    'room_id': room.id,
                    'user_id': user_id,
                    'left_at': None,
                    'is_kicked': False,
                },
            )
        )
        if existing_participant is not None:
            return existing_participant

        active_participants = await self.__room_participant_repository.fetch(
            extra_filters={
                'room_id': room.id,
                'left_at': None,
                'is_kicked': False,
            },
        )
        if len(active_participants) >= room.max_participants:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='The room has reached the maximum number of participants',
            )

        participant = RoomParticipant(
            room_id=room.id,
            user_id=user_id,
            role='participant',
            joined_at=datetime.now(timezone.utc),
            left_at=None,
            is_kicked=False,
        )
        return await self.__room_participant_repository.save(participant)
