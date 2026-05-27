from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from src.app.models.email import EmailAction
from src.tests.utils import (
    login_user,
    read_email_notification,
    read_user_by_email,
    register_user,
    verify_user,
)

NO_REFRESH_COOKIE_ROUTES = [
    ('post', '/api/v1/auth/refresh'),
    ('post', '/api/v1/auth/logout'),
]


async def test_register_rejects_duplicate_user_classes(
    client: AsyncClient,
    user_payload: dict[str, str],
    subtests,
):
    response = await register_user(client, user_payload)

    assert response.status_code == status.HTTP_201_CREATED

    duplicate_cases = {
        'duplicate_email': {
            **user_payload,
            'username': f'{user_payload["username"]}-new',
        },
        'duplicate_username': {
            **user_payload,
            'email': f'new-{user_payload["email"]}',
        },
    }

    for case_name, payload in duplicate_cases.items():
        with subtests.test(msg=case_name):
            duplicate_response = await register_user(client, payload)

            assert duplicate_response.status_code == status.HTTP_409_CONFLICT


async def test_login_rejects_invalid_user_classes(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    subtests,
):
    response = await register_user(client, user_payload)

    assert response.status_code == status.HTTP_201_CREATED

    invalid_cases = {
        'not_verified': {
            'username': user_payload['email'],
            'password': user_payload['password'],
            'status_code': status.HTTP_403_FORBIDDEN,
        },
        'wrong_password': {
            'username': user_payload['email'],
            'password': 'wrong-password',
            'status_code': status.HTTP_401_UNAUTHORIZED,
        },
        'unknown_user': {
            'username': f'missing-{user_payload["email"]}',
            'password': user_payload['password'],
            'status_code': status.HTTP_401_UNAUTHORIZED,
        },
    }

    for case_name, login_data in invalid_cases.items():
        if case_name == 'wrong_password':
            await verify_user(client, session_maker, user_payload)

        with subtests.test(msg=case_name):
            login_response = await client.post('/api/v1/auth/login', data=login_data)

            assert login_response.status_code == login_data['status_code']


@pytest.mark.parametrize(('method', 'url'), NO_REFRESH_COOKIE_ROUTES)
async def test_refresh_and_logout_require_refresh_cookie(
    client: AsyncClient,
    method: str,
    url: str,
):
    response = await client.request(method, url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_verify_account_rejects_unknown_notification(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)

    assert response.status_code == status.HTTP_201_CREATED

    user = await read_user_by_email(session_maker, user_payload['email'])
    verify_response = await client.get(
        f'/api/v1/auth/user/{user.id}/verify',
        params={'code': str(uuid4())},
    )

    assert verify_response.status_code == status.HTTP_404_NOT_FOUND


async def test_verify_account_rejects_reused_notification(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)
    assert response.status_code == status.HTTP_201_CREATED

    user = await read_user_by_email(session_maker, user_payload['email'])
    notification = await read_email_notification(session_maker, user.id)
    verify_response = await client.get(
        f'/api/v1/auth/user/{user.id}/verify',
        params={'code': str(notification.code)},
    )
    assert verify_response.status_code == status.HTTP_200_OK

    reused_response = await client.get(
        f'/api/v1/auth/user/{user.id}/verify',
        params={'code': str(notification.code)},
    )
    assert reused_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_password_reset_send_code_rejects_unknown_user(client: AsyncClient):
    response = await client.get(f'/api/v1/auth/user/{uuid4()}/password-reset/send-code')

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_refresh_rotates_tokens_and_logout_revokes_session(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)
    assert response.status_code == status.HTTP_201_CREATED

    await verify_user(client, session_maker, user_payload)
    login_response = await login_user(client, user_payload)
    token_data = login_response.json()

    refresh_response = await client.post('/api/v1/auth/refresh')

    assert refresh_response.status_code == status.HTTP_200_OK
    refreshed_token_data = refresh_response.json()
    assert refreshed_token_data['refresh_token'] != token_data['refresh_token']

    logout_response = await client.post('/api/v1/auth/logout')

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json() == {'success': True}


async def test_current_user_profile_returns_verified_user(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)
    assert response.status_code == status.HTTP_201_CREATED

    user = await verify_user(client, session_maker, user_payload)
    login_response = await login_user(client, user_payload)
    access_token = login_response.json()['access_token']

    profile_response = await client.get(
        '/api/v1/users/me',
        headers={'Authorization': f'Bearer {access_token}'},
    )

    assert profile_response.status_code == status.HTTP_200_OK
    assert profile_response.json()['id'] == str(user.id)


async def test_password_reset_changes_password_and_revokes_sessions(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)
    assert response.status_code == status.HTTP_201_CREATED

    user = await verify_user(client, session_maker, user_payload)
    login_response = await login_user(client, user_payload)
    assert login_response.status_code == status.HTTP_200_OK

    send_code_response = await client.get(
        f'/api/v1/auth/user/{user.id}/password-reset/send-code'
    )

    assert send_code_response.status_code == status.HTTP_200_OK

    notification = await read_email_notification(
        session_maker,
        user.id,
        EmailAction.CHANGE_PASSWORD,
    )
    new_password = 'new-test-password-123'

    reset_response = await client.post(
        f'/api/v1/auth/user/{user.id}/password-reset/confirm',
        json={
            'code': str(notification.code),
            'new_password': new_password,
            'repeat_password': new_password,
        },
    )

    assert reset_response.status_code == status.HTTP_200_OK
    assert reset_response.json() == {'success': True}

    old_password_response = await login_user(client, user_payload)
    assert old_password_response.status_code == status.HTTP_401_UNAUTHORIZED

    new_password_response = await login_user(
        client,
        {
            **user_payload,
            'password': new_password,
        },
    )
    assert new_password_response.status_code == status.HTTP_200_OK


async def test_password_reset_rejects_mismatched_passwords(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    response = await register_user(client, user_payload)
    assert response.status_code == status.HTTP_201_CREATED

    user = await verify_user(client, session_maker, user_payload)
    send_code_response = await client.get(
        f'/api/v1/auth/user/{user.id}/password-reset/send-code'
    )
    assert send_code_response.status_code == status.HTTP_200_OK

    notification = await read_email_notification(
        session_maker,
        user.id,
        EmailAction.CHANGE_PASSWORD,
    )
    reset_response = await client.post(
        f'/api/v1/auth/user/{user.id}/password-reset/confirm',
        json={
            'code': str(notification.code),
            'new_password': 'new-test-password-123',
            'repeat_password': 'other-test-password-123',
        },
    )

    assert reset_response.status_code == status.HTTP_400_BAD_REQUEST
