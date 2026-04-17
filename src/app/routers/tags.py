from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query

from src.app.dependencies.security import (
    CurrentUserTagsDeleteDep,
    CurrentUserTagsReadDep,
    CurrentUserTagsWriteDep,
)
from src.app.dependencies.services import TagServiceDep
from src.app.models.tag import TagCreate, TagPublic, TagUpdate
from src.app.schemas.tag_filters import TagFilters

router = APIRouter(
    prefix='/tags',
    tags=['tags'],
)


@router.get('/')
async def get_tags(
    filters: Annotated[TagFilters, Query()],
    tag_service: TagServiceDep,
    _current_user: CurrentUserTagsReadDep,
) -> Sequence[TagPublic]:
    return await tag_service.get_tags(filters)


@router.post('/')
async def create_tag(
    tag_create: TagCreate,
    tag_service: TagServiceDep,
    _current_user: CurrentUserTagsWriteDep,
) -> TagPublic:
    return await tag_service.create_tag(tag_create)


@router.get('/{tag_id}')
async def get_tag(
    tag_id: UUID,
    tag_service: TagServiceDep,
    _current_user: CurrentUserTagsReadDep,
) -> Optional[TagPublic]:
    return await tag_service.get_tag(tag_id)


@router.put('/{tag_id}')
async def update_tag(
    tag_update: TagUpdate,
    tag_id: UUID,
    tag_service: TagServiceDep,
    _current_user: CurrentUserTagsWriteDep,
) -> Optional[TagPublic]:
    return await tag_service.update_tag(tag_update, tag_id)


@router.delete('/{tag_id}')
async def delete_tag(
    tag_id: UUID,
    tag_service: TagServiceDep,
    _current_user: CurrentUserTagsDeleteDep,
) -> Optional[TagPublic]:
    return await tag_service.delete_tag(tag_id)
