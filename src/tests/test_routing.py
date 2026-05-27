from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from src.app.core.settings import settings
from src.tests.utils import register_verified_user

pytestmark = pytest.mark.asyncio

ROOM_ID = uuid4()
ELEMENT_ID = uuid4()
COMMENT_ID = uuid4()
MESSAGE_ID = uuid4()
PROJECT_ID = uuid4()
TAG_ID = uuid4()
USER_ID = uuid4()

PROTECTED_ROUTES = [
    ('get', '/api/v1/users/me'),
    ('get', f'/api/v1/users/{USER_ID}'),
    ('post', f'/api/v1/users/{USER_ID}/roles/{settings.rbac.admin_role}'),
    ('get', '/api/v1/projects/'),
    ('post', '/api/v1/projects/'),
    ('get', f'/api/v1/projects/{PROJECT_ID}'),
    ('put', f'/api/v1/projects/{PROJECT_ID}'),
    ('delete', f'/api/v1/projects/{PROJECT_ID}'),
    ('get', f'/api/v1/projects/{PROJECT_ID}/tags'),
    ('post', f'/api/v1/projects/{PROJECT_ID}/tags/{TAG_ID}'),
    ('delete', f'/api/v1/projects/{PROJECT_ID}/tags/{TAG_ID}'),
    ('get', '/api/v1/tags/'),
    ('post', '/api/v1/tags/'),
    ('get', f'/api/v1/tags/{TAG_ID}'),
    ('put', f'/api/v1/tags/{TAG_ID}'),
    ('delete', f'/api/v1/tags/{TAG_ID}'),
    ('get', '/api/v1/rooms/'),
    ('post', '/api/v1/rooms/'),
    ('post', '/api/v1/rooms/join'),
    ('put', f'/api/v1/rooms/{ROOM_ID}'),
    ('delete', f'/api/v1/rooms/{ROOM_ID}'),
    ('get', f'/api/v1/rooms/{ROOM_ID}/participants/'),
    ('patch', f'/api/v1/rooms/{ROOM_ID}/participants/{USER_ID}'),
    ('delete', f'/api/v1/rooms/{ROOM_ID}/participants/{USER_ID}'),
    ('get', f'/api/v1/rooms/{ROOM_ID}/messages/'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/messages/'),
    ('put', f'/api/v1/rooms/{ROOM_ID}/messages/{MESSAGE_ID}'),
    ('delete', f'/api/v1/rooms/{ROOM_ID}/messages/{MESSAGE_ID}'),
    ('get', f'/api/v1/rooms/{ROOM_ID}/board-elements/'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/board-elements/'),
    ('put', f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}'),
    ('delete', f'/api/v1/rooms/{ROOM_ID}/board-elements/'),
    ('delete', f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}'),
    ('get', f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}/comments/'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}/comments/'),
    (
        'put',
        (f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}/comments/{COMMENT_ID}'),
    ),
    (
        'delete',
        (f'/api/v1/rooms/{ROOM_ID}/board-elements/{ELEMENT_ID}/comments/{COMMENT_ID}'),
    ),
    ('get', f'/api/v1/rooms/{ROOM_ID}/pomodoro/'),
    ('patch', f'/api/v1/rooms/{ROOM_ID}/pomodoro/settings'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/pomodoro/start'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/pomodoro/pause'),
    ('post', f'/api/v1/rooms/{ROOM_ID}/pomodoro/reset'),
]


@pytest.mark.parametrize(('method', 'url'), PROTECTED_ROUTES)
async def test_protected_routes_require_authentication(
    client: AsyncClient,
    method: str,
    url: str,
):
    response = await client.request(method, url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_public_user_cannot_access_admin_routes(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    auth = await register_verified_user(client, session_maker, user_payload)

    tag_response = await client.post(
        '/api/v1/tags/',
        headers=auth.headers,
        json={
            'name': 'blocked',
            'color': '#FFFFFF',
            'description': 'Should not be created',
        },
    )
    assert tag_response.status_code == status.HTTP_403_FORBIDDEN

    role_response = await client.post(
        f'/api/v1/users/{auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=auth.headers,
    )
    assert role_response.status_code == status.HTTP_403_FORBIDDEN


async def test_missing_resources_return_expected_404(
    client: AsyncClient,
    admin_auth,
):
    missing_id = uuid4()
    tag_update_payload = {
        'name': 'missing',
        'color': '#000000',
        'description': 'Missing tag',
    }

    cases = [
        ('get', f'/api/v1/users/{missing_id}', None),
        ('get', f'/api/v1/tags/{missing_id}', None),
        ('put', f'/api/v1/tags/{missing_id}', tag_update_payload),
        ('delete', f'/api/v1/tags/{missing_id}', None),
    ]

    for method, url, json in cases:
        response = await client.request(
            method,
            url,
            headers=admin_auth.headers,
            json=json,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_invalid_payloads_return_validation_errors(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    auth = await register_verified_user(client, session_maker, user_payload)

    project_response = await client.post(
        '/api/v1/projects/',
        headers=auth.headers,
        json={'title': 'missing required roles shape', 'required_roles': 'backend'},
    )
    assert project_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    room_response = await client.post(
        '/api/v1/rooms/join',
        headers=auth.headers,
        json={'wrong_field': 'ABC123'},
    )
    assert room_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_invalid_access_token_is_rejected(client: AsyncClient):
    response = await client.get(
        '/api/v1/users/me',
        headers={'Authorization': 'Bearer invalid-token'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
