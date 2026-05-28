import pytest
from fastapi import status
from httpx import AsyncClient

PUBLIC_URLS = [
    '/health',
    '/docs',
    '/openapi.json',
]


@pytest.mark.parametrize('url', PUBLIC_URLS)
async def test_public_urls_are_available(async_client: AsyncClient, url: str):
    response = await async_client.get(url)

    assert response.status_code == status.HTTP_200_OK


async def test_unknown_url_returns_404(async_client: AsyncClient):
    response = await async_client.get('/missing-url')

    assert response.status_code == status.HTTP_404_NOT_FOUND
