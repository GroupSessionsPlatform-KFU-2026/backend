import json
from pathlib import Path
from uuid import UUID

from fastapi import status
from httpx import AsyncClient
from sqlmodel import select
from src.app.models.email import EmailAction, EmailNotification
from src.app.models.user import User

TEST_DATA_DIR = Path(__file__).parent / 'data'


def read_data(file_name: str) -> dict:
    return json.loads((TEST_DATA_DIR / file_name).read_text(encoding='utf-8'))


async def read_user_by_email(session_maker, email: str) -> User:
    async with session_maker() as session:
        result = await session.exec(select(User).where(User.email == email))
        return result.one()


async def read_email_notification(
    session_maker,
    user_id: UUID,
    action: EmailAction = EmailAction.VERIFY_ACCOUNT,
) -> EmailNotification:
    async with session_maker() as session:
        result = await session.exec(
            select(EmailNotification).where(
                EmailNotification.user_id == user_id,
                EmailNotification.action == action,
            )
        )
        return result.one()


async def register_user(client: AsyncClient, user_payload: dict[str, str]):
    return await client.post('/api/v1/auth/register', json=user_payload)


async def verify_user(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
) -> User:
    user = await read_user_by_email(session_maker, user_payload['email'])
    notification = await read_email_notification(session_maker, user.id)

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


async def build_auth_context(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
) -> dict:
    register_response = await register_user(client, user_payload)
    assert register_response.status_code == status.HTTP_201_CREATED

    user = await verify_user(client, session_maker, user_payload)
    login_response = await login_user(client, user_payload)
    assert login_response.status_code == status.HTTP_200_OK

    token_data = login_response.json()
    return {
        'user': user,
        'payload': user_payload,
        'tokens': token_data,
        'headers': {'Authorization': f'Bearer {token_data["access_token"]}'},
    }
