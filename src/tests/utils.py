import json
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from fastapi import status
from httpx import AsyncClient
from src.app.models.email import EmailAction, EmailNotification
from src.app.models.user import User
from src.app.services.users import UserService
from src.app.utils.repository import Repository
from src.app.utils.user_repository import UserRepository

TEST_DATA_DIR = Path(__file__).parent / 'data'


@dataclass(slots=True)
class AuthContext:
    user: User
    payload: dict[str, str]
    tokens: dict
    headers: dict[str, str]
    scopes: set[str] = field(default_factory=set)


def read_data(file_name: str) -> dict:
    return json.loads((TEST_DATA_DIR / file_name).read_text(encoding='utf-8'))


async def get_user_by_email(session_maker, email: str) -> User:
    async with session_maker() as session:
        user_service = UserService(UserRepository(session))
        user = await user_service.get_user_by_email(email)
        if user is None:
            raise AssertionError(f'User with email {email} was not found')
        return user


async def get_email_notification(
    session_maker,
    user_id: UUID,
    action: EmailAction = EmailAction.VERIFY_ACCOUNT,
) -> EmailNotification:
    async with session_maker() as session:
        repository = Repository[EmailNotification](session)
        notification = await repository.get_one_by_filters(
            extra_filters={
                'user_id': user_id,
                'action': action,
            },
        )
        if notification is None:
            raise AssertionError(
                f'Email notification {action} for user {user_id} was not found'
            )
        return notification


async def register_user(client: AsyncClient, user_payload: dict[str, str]):
    return await client.post('/api/v1/auth/register', json=user_payload)


async def verify_user(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
) -> User:
    user = await get_user_by_email(session_maker, user_payload['email'])
    notification = await get_email_notification(session_maker, user.id)

    response = await client.get(
        f'/api/v1/auth/user/{user.id}/verify',
        params={'code': str(notification.code)},
    )
    assert response.status_code == status.HTTP_200_OK

    return user


async def login_user(client: AsyncClient, user_payload: dict[str, str]):
    return await client.post(
        '/api/v1/auth/login',
        data={
            'username': user_payload['email'],
            'password': user_payload['password'],
        },
    )


async def register_verified_user(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
) -> AuthContext:
    register_response = await register_user(client, user_payload)
    assert register_response.status_code == status.HTTP_201_CREATED

    user = await verify_user(client, session_maker, user_payload)
    login_response = await login_user(client, user_payload)
    assert login_response.status_code == status.HTTP_200_OK

    token_data = login_response.json()
    return AuthContext(
        user=user,
        payload=user_payload,
        tokens=token_data,
        headers={'Authorization': f'Bearer {token_data["access_token"]}'},
    )
