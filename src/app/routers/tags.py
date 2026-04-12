from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Depends

from fastapi import APIRouter, Query, Security
from src.app.dependencies.security import get_current_user
from src.app.models.user import User
from src.app.services.tags import TagService
from src.app.models.tag import TagCreate, TagPublic, TagUpdate
from src.app.schemas.tag_filters import TagFilters

router = APIRouter(
    prefix='/tags',
    tags=['tags'],
)


@router.get('/')
async def get_tags(
    filters: Annotated[TagFilters, Query()],
    tag_service: TagService = Depends(),
    current_user: User = Security(get_current_user, scopes=['tags:read']),
) -> Sequence[TagPublic]:
    return await tag_service.get_tags(filters)


@router.post('/')
async def create_tag(
    tag_create: TagCreate,
    tag_service: TagService = Depends(),
    current_user: User = Security(get_current_user, scopes=['tags:write']),
) -> TagPublic:
    return await tag_service.create_tag(tag_create)


@router.get('/{tag_id}')
async def get_tag(
    tag_id: UUID,
    tag_service: TagService = Depends(),
    current_user: User = Security(get_current_user, scopes=['tags:read']),
) -> Optional[TagPublic]:
    return await tag_service.get_tag(tag_id)


@router.put('/{tag_id}')
async def update_tag(
    tag_update: TagUpdate,
    tag_id: UUID,
    tag_service: TagService = Depends(),
    current_user: User = Security(get_current_user, scopes=['tags:write']),
) -> Optional[TagPublic]:
    return await tag_service.update_tag(tag_update, tag_id)


@router.delete('/{tag_id}')
async def delete_tag(
    tag_id: UUID,
    tag_service: TagService = Depends(),
    current_user: User = Security(get_current_user, scopes=['tags:delete']),
) -> Optional[TagPublic]:
    return await tag_service.delete_tag(tag_id)
