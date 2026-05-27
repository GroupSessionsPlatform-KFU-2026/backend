import pytest
from fastapi import status
from httpx import AsyncClient
from src.app.core.settings import settings

pytestmark = pytest.mark.asyncio


async def test_public_access_token_can_read_own_profile(
    async_client: AsyncClient,
    public_access_token: str,
    public_auth,
):
    response = await async_client.get(
        '/api/v1/users/me',
        headers={'Authorization': f'Bearer {public_access_token}'},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == str(public_auth.user.id)


async def test_public_access_token_has_public_scopes(
    public_access_token: str,
    public_scopes: set[str],
):
    assert public_access_token
    assert 'profile:read' in public_scopes
    assert 'projects:read' in public_scopes
    assert 'tags:write' not in public_scopes


async def test_admin_access_token_can_assign_roles(
    async_client: AsyncClient,
    admin_headers: dict[str, str],
    public_auth,
):
    response = await async_client.post(
        f'/api/v1/users/{public_auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=admin_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'success': True}


async def test_admin_access_token_has_admin_scopes(
    admin_access_token: str,
    admin_scopes: set[str],
):
    assert admin_access_token
    assert 'users:write' in admin_scopes
    assert 'tags:write' in admin_scopes
    assert 'users:delete' in admin_scopes


async def test_public_access_token_cannot_assign_roles(
    async_client: AsyncClient,
    public_headers: dict[str, str],
    public_auth,
):
    response = await async_client.post(
        f'/api/v1/users/{public_auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=public_headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
