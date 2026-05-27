from collections.abc import AsyncGenerator
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.app.core.limiter import limiter
from src.app.core.rbac import INITIAL_ROLE_SCOPES, PERMISSION_DESCRIPTIONS
from src.app.core.settings import settings
from src.app.db.engine import form_test_db_url
from src.app.dependencies.session import get_session
from src.app.main import fastapi_app
from src.app.models.role import Role
from src.app.models.user import User
from src.app.models.user_role import UserRoleLink
from src.app.services.email import EmailService
from src.app.utils.hashing import get_password_hash
from src.test_db_init import drop_test_db, init_test_db
from src.tests.utils import build_auth_context

import_module('src.app.models')


class FakeEmailService:
    def send_email(self, email_data) -> None:
        _ = email_data


@pytest_asyncio.fixture
async def async_db_engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine]:
    database_url = form_test_db_url(str(tmp_path / 'test.db'))
    db_engine = create_async_engine(
        database_url,
        connect_args={'check_same_thread': False},
    )
    yield db_engine
    await db_engine.dispose()


@pytest_asyncio.fixture
async def async_session(
    async_db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def async_db(
    async_session: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    await init_test_db(async_session)

    yield async_session

    await drop_test_db(async_session)


@pytest_asyncio.fixture
async def session_maker(
    async_db: async_sessionmaker[AsyncSession],
) -> async_sessionmaker[AsyncSession]:
    return async_db


@pytest_asyncio.fixture
async def async_client(
    async_db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient]:
    async def override_get_session():
        async with async_db() as session:
            yield session

    fastapi_app.dependency_overrides[get_session] = override_get_session
    fastapi_app.dependency_overrides[EmailService] = FakeEmailService
    previous_limiter_state = limiter.enabled
    limiter.enabled = False

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url='http://test') as http_client:
        yield http_client

    limiter.enabled = previous_limiter_state
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(async_client: AsyncClient) -> AsyncClient:
    return async_client


@pytest.fixture
def user_payload() -> dict[str, str]:
    user_id = uuid4().hex
    return {
        'email': f'test-{user_id}@example.com',
        'username': f'test-{user_id}',
        'password': 'test-password-123',
    }


@pytest.fixture
def second_user_payload() -> dict[str, str]:
    user_id = uuid4().hex
    return {
        'email': f'second-{user_id}@example.com',
        'username': f'second-{user_id}',
        'password': 'test-password-123',
    }


@pytest_asyncio.fixture
async def public_auth(
    async_client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
):
    auth_context = await build_auth_context(async_client, session_maker, user_payload)
    auth_context['scopes'] = set(INITIAL_ROLE_SCOPES[settings.rbac.public_role])
    return auth_context


@pytest.fixture
def public_access_token(public_auth) -> str:
    return public_auth['tokens']['access_token']


@pytest.fixture
def public_scopes(public_auth) -> set[str]:
    return public_auth['scopes']


@pytest.fixture
def public_headers(public_access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {public_access_token}'}


@pytest_asyncio.fixture
async def admin_auth(client: AsyncClient, session_maker):
    admin_id = uuid4().hex
    payload = {
        'email': f'admin-{admin_id}@example.com',
        'username': f'admin-{admin_id}',
        'password': 'admin-password-123',
    }

    async with session_maker() as session:
        admin_role = (
            await session.exec(
                select(Role).where(Role.name == settings.rbac.admin_role)
            )
        ).one()
        admin_user = User(
            email=payload['email'],
            username=payload['username'],
            avatar_url=None,
            password_hash=get_password_hash(payload['password']),
            is_active=True,
            is_verified=True,
        )
        session.add(admin_user)
        await session.flush()
        session.add(UserRoleLink(user_id=admin_user.id, role_id=admin_role.id))
        await session.commit()
        await session.refresh(admin_user)

    login_response = await client.post(
        '/api/v1/auth/login',
        data={
            'username': payload['email'],
            'password': payload['password'],
        },
    )
    token_data = login_response.json()

    return {
        'user': admin_user,
        'payload': payload,
        'tokens': token_data,
        'headers': {'Authorization': f'Bearer {token_data["access_token"]}'},
        'scopes': set(PERMISSION_DESCRIPTIONS),
    }


@pytest.fixture
def admin_access_token(admin_auth) -> str:
    return admin_auth['tokens']['access_token']


@pytest.fixture
def admin_scopes(admin_auth) -> set[str]:
    return admin_auth['scopes']


@pytest.fixture
def admin_headers(admin_access_token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {admin_access_token}'}
