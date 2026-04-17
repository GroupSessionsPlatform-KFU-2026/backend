from dataclasses import dataclass
from uuid import UUID

from socketio.exceptions import ConnectionRefusedError as SocketConnectionRefusedError

from src.app.dependencies.session import async_session_maker
from src.app.models.refresh_session import RefreshSession
from src.app.models.role import Role
from src.app.models.room import Room, RoomStatus
from src.app.models.room_participant import RoomParticipant
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.services.auth import AuthService
from src.app.services.users import UserService
from src.app.utils.repository import Repository
from src.app.utils.user_repository import UserRepository


@dataclass(slots=True)
class SocketAuthContext:
    user_id: UUID
    room_id: UUID
    role: str
    scopes: list[str]


def _extract_access_token(auth: object) -> str:
    if not isinstance(auth, dict):
        raise SocketConnectionRefusedError('Missing socket auth payload')

    access_token = auth.get('access_token')
    if not isinstance(access_token, str) or not access_token.strip():
        raise SocketConnectionRefusedError('Missing access token')

    return access_token


def _extract_room_id(auth: object) -> UUID:
    if not isinstance(auth, dict):
        raise SocketConnectionRefusedError('Missing socket auth payload')

    raw_room_id = auth.get('room_id')
    if raw_room_id is None:
        raise SocketConnectionRefusedError('Missing room id')

    try:
        return UUID(str(raw_room_id))
    except ValueError as error:
        raise SocketConnectionRefusedError('Invalid room id') from error


def _collect_user_scopes(user: User) -> list[str]:
    scopes = {
        permission.scope for role in user.roles for permission in role.permissions
    }
    return sorted(scopes)


async def authenticate_socket_connection(auth: object) -> SocketAuthContext:
    access_token = _extract_access_token(auth)
    room_id = _extract_room_id(auth)

    async with async_session_maker() as session:
        user_repository = UserRepository(session)
        refresh_session_repository = Repository[RefreshSession](session)
        role_repository = Repository[Role](session)
        user_role_repository = Repository[UserRoleLink](session)
        room_repository = Repository[Room](session)
        room_participant_repository = Repository[RoomParticipant](session)

        user_service = UserService(user_repository=user_repository)
        auth_service = AuthService(
            user_repository=user_repository,
            refresh_session_repository=refresh_session_repository,
            role_repository=role_repository,
            user_role_repository=user_role_repository,
            user_service=user_service,
        )

        try:
            user = await auth_service.get_current_user(
                token=access_token,
                required_scopes=['rooms:read'],
            )
        except Exception as error:
            raise SocketConnectionRefusedError('Invalid access token') from error

        scopes = _collect_user_scopes(user)

        room = await room_repository.get(room_id)
        if room is None:
            raise SocketConnectionRefusedError('Room not found')

        if room.status == RoomStatus.ENDED:
            raise SocketConnectionRefusedError('Room already ended')

        if room.creator_id == user.id:
            return SocketAuthContext(
                user_id=user.id,
                room_id=room.id,
                role='owner',
                scopes=scopes,
            )

        participants = await room_participant_repository.fetch(
            extra_filters={
                'room_id': room.id,
                'user_id': user.id,
            }
        )

        active_participant = next(
            (
                participant
                for participant in participants
                if not participant.is_kicked and participant.left_at is None
            ),
            None,
        )

        if active_participant is None:
            raise SocketConnectionRefusedError('User has no access to this room')

        return SocketAuthContext(
            user_id=user.id,
            room_id=room.id,
            role=active_participant.role,
            scopes=scopes,
        )
