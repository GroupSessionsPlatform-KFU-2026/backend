from typing import Annotated, Optional, Sequence
from uuid import UUID

from fastapi import APIRouter, Query, Security

from src.app.dependencies.security import require_scoped_user
from src.app.dependencies.services import TagServiceDep
from src.app.models.tag import TagCreate, TagPublic, TagUpdate
from src.app.schemas.tag_filters import TagFilters
from src.app.core.responses import auth_responses, detail_responses
from src.app.utils.errors import NotFoundError

router = APIRouter(
    prefix='/tags',
    tags=['tags'],
)


@router.get('/', dependencies=[Security(require_scoped_user, scopes=['tags:read'])], responses=auth_responses,)
async def get_tags(
    filters: Annotated[TagFilters, Query()],
    tag_service: TagServiceDep,
) -> Sequence[TagPublic]:
    return await tag_service.get_tags(filters)


@router.post('/', dependencies=[Security(require_scoped_user, scopes=['tags:write'])], responses=auth_responses,)
async def create_tag(
    tag_create: TagCreate,
    tag_service: TagServiceDep,
) -> TagPublic:
    return await tag_service.create_tag(tag_create)


@router.get(
    '/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['tags:read'])],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def get_tag(
    tag_id: UUID,
    tag_service: TagServiceDep,
) -> TagPublic:
    tag = await tag_service.get_tag(tag_id)

    if tag is None:
        raise NotFoundError

    return tag


@router.put(
    '/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['tags:write'])],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def update_tag(
    tag_update: TagUpdate,
    tag_id: UUID,
    tag_service: TagServiceDep,
) -> TagPublic:
    tag = await tag_service.update_tag(tag_update, tag_id)

    if tag is None:
        raise NotFoundError

    return tag


@router.delete(
    '/{tag_id}',
    dependencies=[Security(require_scoped_user, scopes=['tags:delete'])],
    responses={
        **auth_responses,
        **detail_responses,
    },
)
async def delete_tag(
    tag_id: UUID,
    tag_service: TagServiceDep,
) -> TagPublic:
    tag = await tag_service.delete_tag(tag_id)

    if tag is None:
        raise NotFoundError

    return tag
