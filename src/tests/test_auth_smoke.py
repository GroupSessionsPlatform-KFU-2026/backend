import pytest
from fastapi import status
from httpx import AsyncClient
from sqlmodel import select
from src.app.models.email import EmailAction, EmailNotification
from src.app.models.user import User


@pytest.mark.smoke
async def test_register_verify_login_logout_smoke(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    register_response = await client.post('/api/v1/auth/register', json=user_payload)

    assert register_response.status_code == status.HTTP_201_CREATED
    assert register_response.json() == {'success': True}

    async with session_maker() as session:
        user_result = await session.exec(
            select(User).where(User.email == user_payload['email'])
        )
        user = user_result.one()

        notification_result = await session.exec(
            select(EmailNotification).where(
                EmailNotification.user_id == user.id,
                EmailNotification.action == EmailAction.VERIFY_ACCOUNT,
            )
        )
        notification = notification_result.one()

    verify_response = await client.get(
        f'/api/v1/auth/user/{user.id}/verify',
        params={'code': str(notification.code)},
    )

    assert verify_response.status_code == status.HTTP_200_OK
    assert verify_response.json() == {'success': True}

    login_response = await client.post(
        '/api/v1/auth/login',
        data={
            'username': user_payload['email'],
            'password': user_payload['password'],
        },
    )

    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    assert token_data['access_token']
    assert token_data['refresh_token']
    assert token_data['token_type'] == 'bearer'

    logout_response = await client.post('/api/v1/auth/logout')

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {'success': True}
