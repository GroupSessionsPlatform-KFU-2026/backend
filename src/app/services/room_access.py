from uuid import UUID

from fastapi import HTTPException, status

from src.app.dependencies.repositories import (
    BoardElementCommentRepositoryDep,
    BoardElementRepositoryDep,
    ChatMessageRepositoryDep,
    RoomParticipantRepositoryDep,
    RoomRepositoryDep,
)


class RoomAccessService:
    def __init__(
        self,
        room_repository: RoomRepositoryDep,
        room_participant_repository: RoomParticipantRepositoryDep,
        chat_message_repository: ChatMessageRepositoryDep,
        board_element_repository: BoardElementRepositoryDep,
        board_element_comment_repository: BoardElementCommentRepositoryDep,
    ):
        self.__room_repository = room_repository
        self.__room_participant_repository = room_participant_repository
        self.__chat_message_repository = chat_message_repository
        self.__board_element_repository = board_element_repository
        self.__board_element_comment_repository = board_element_comment_repository

    async def get_actor_role(self, room_id: UUID, user_id: UUID) -> str:
        room = await self.__room_repository.get(room_id)
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Room not found',
            )

        if room.creator_id == user_id:
            return 'owner'

        participant = await self.__room_participant_repository.get_one_by_filters(
            extra_filters={
                'room_id': room_id,
                'user_id': user_id,
                'left_at': None,
                'is_kicked': False,
            },
        )
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have access to this room',
            )

        return participant.role

    async def ensure_room_access(self, room_id: UUID, user_id: UUID) -> None:
        await self.get_actor_role(room_id, user_id)

    async def ensure_can_moderate(self, room_id: UUID, user_id: UUID) -> None:
        role = await self.get_actor_role(room_id, user_id)
        if role not in {'owner', 'moderator'}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only owner or moderator can perform this action',
            )

    async def ensure_message_manage(
        self,
        room_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> None:
        role = await self.get_actor_role(room_id, user_id)

        message = await self.__chat_message_repository.get_one_by_filters(
            extra_filters={
                'id': message_id,
                'room_id': room_id,
            },
        )
        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Message not found',
            )

        can_manage = message.sender_id == user_id or role in {'owner', 'moderator'}
        if not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can edit/delete only your own messages',
            )

    async def ensure_board_element_manage(
        self,
        room_id: UUID,
        element_id: UUID,
        user_id: UUID,
    ) -> None:
        role = await self.get_actor_role(room_id, user_id)

        element = await self.__board_element_repository.get_one_by_filters(
            extra_filters={
                'id': element_id,
                'room_id': room_id,
            },
        )
        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        can_manage = element.author_id == user_id or role in {'owner', 'moderator'}
        if not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can edit/delete only your own board elements',
            )

    async def ensure_comment_manage(
        self,
        room_id: UUID,
        element_id: UUID,
        comment_id: UUID,
        user_id: UUID,
    ) -> None:
        role = await self.get_actor_role(room_id, user_id)

        element = await self.__board_element_repository.get_one_by_filters(
            extra_filters={
                'id': element_id,
                'room_id': room_id,
            },
        )
        if element is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Board element not found',
            )

        comment = await self.__board_element_comment_repository.get_one_by_filters(
            extra_filters={
                'id': comment_id,
                'board_element_id': element_id,
            },
        )
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Comment not found',
            )

        can_manage = comment.author_id == user_id or role in {'owner', 'moderator'}
        if not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can edit/delete only your own comments',
            )
