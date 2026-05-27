import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_healthcheck_returns_ok(client: AsyncClient):
    response = await client.get('/health')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': 'ok'}
