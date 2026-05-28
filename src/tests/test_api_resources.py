from fastapi import status
from httpx import AsyncClient
from src.app.core.settings import settings
from src.tests.utils import read_data, register_verified_user

EXPECTED_BOARD_ELEMENTS = 2
UPDATED_WORK_DURATION = 30


async def create_project(client: AsyncClient, headers: dict[str, str]) -> dict:
    response = await client.post(
        '/api/v1/projects/',
        headers=headers,
        json=read_data('project_create.json'),
    )

    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def create_room(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
) -> dict:
    payload = read_data('room_create.json')
    payload['project_id'] = project_id

    response = await client.post(
        '/api/v1/rooms/',
        headers=headers,
        json=payload,
    )

    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def test_project_and_tag_flow(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    admin_auth,
):
    auth = await register_verified_user(client, session_maker, user_payload)
    project = await create_project(client, auth.headers)

    list_response = await client.get('/api/v1/projects/', headers=auth.headers)
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.json()['info']['total'] == 1

    get_response = await client.get(
        f'/api/v1/projects/{project["id"]}',
        headers=auth.headers,
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()['title'] == project['title']

    update_response = await client.put(
        f'/api/v1/projects/{project["id"]}',
        headers=auth.headers,
        json={'title': 'Updated project'},
    )
    assert update_response.status_code == status.HTTP_200_OK
    assert update_response.json()['title'] == 'Updated project'

    tag_response = await client.post(
        '/api/v1/tags/',
        headers=admin_auth.headers,
        json={
            'name': 'backend',
            'color': '#00AAFF',
            'description': 'Backend tasks',
        },
    )
    assert tag_response.status_code == status.HTTP_200_OK
    tag = tag_response.json()

    tag_list_response = await client.get('/api/v1/tags/', headers=auth.headers)
    assert tag_list_response.status_code == status.HTTP_200_OK
    assert tag_list_response.json()['info']['total'] == 1

    tag_get_response = await client.get(
        f'/api/v1/tags/{tag["id"]}',
        headers=auth.headers,
    )
    assert tag_get_response.status_code == status.HTTP_200_OK
    assert tag_get_response.json()['name'] == 'backend'

    tag_update_response = await client.put(
        f'/api/v1/tags/{tag["id"]}',
        headers=admin_auth.headers,
        json={
            'name': 'backend-updated',
            'color': '#22CC88',
            'description': 'Updated backend tasks',
        },
    )
    assert tag_update_response.status_code == status.HTTP_200_OK

    assign_response = await client.post(
        f'/api/v1/projects/{project["id"]}/tags/{tag["id"]}',
        headers=auth.headers,
    )
    assert assign_response.status_code == status.HTTP_200_OK
    assert assign_response.json()['is_active'] is True

    project_tags_response = await client.get(
        f'/api/v1/projects/{project["id"]}/tags',
        headers=auth.headers,
    )
    assert project_tags_response.status_code == status.HTTP_200_OK
    assert len(project_tags_response.json()) == 1

    remove_tag_response = await client.delete(
        f'/api/v1/projects/{project["id"]}/tags/{tag["id"]}',
        headers=auth.headers,
    )
    assert remove_tag_response.status_code == status.HTTP_200_OK

    delete_tag_response = await client.delete(
        f'/api/v1/tags/{tag["id"]}',
        headers=admin_auth.headers,
    )
    assert delete_tag_response.status_code == status.HTTP_200_OK

    archive_response = await client.delete(
        f'/api/v1/projects/{project["id"]}',
        headers=auth.headers,
    )
    assert archive_response.status_code == status.HTTP_200_OK
    assert archive_response.json()['is_archived'] is True


async def test_empty_list_endpoints_return_paginated_content_schema(
    client: AsyncClient,
    public_headers: dict[str, str],
):
    urls = [
        '/api/v1/projects/',
        '/api/v1/rooms/',
        '/api/v1/tags/',
    ]

    for url in urls:
        response = await client.get(url, headers=public_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            'info': {
                'page': 1,
                'pages_num': 0,
                'total': 0,
            },
            'items': [],
        }


async def test_room_chat_board_comments_and_pomodoro_flow(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
):
    owner = await register_verified_user(client, session_maker, user_payload)
    participant = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    project = await create_project(client, owner.headers)
    room = await create_room(client, owner.headers, project['id'])

    room_list_response = await client.get('/api/v1/rooms/', headers=owner.headers)
    assert room_list_response.status_code == status.HTTP_200_OK
    assert room_list_response.json()['info']['total'] == 1

    join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant.headers,
        json={'room_code': room['room_code']},
    )
    assert join_response.status_code == status.HTTP_200_OK
    assert join_response.json()['role'] == 'participant'

    participants_response = await client.get(
        f'/api/v1/rooms/{room["id"]}/participants/',
        headers=owner.headers,
    )
    assert participants_response.status_code == status.HTTP_200_OK
    assert participants_response.json()['info']['total'] == 1

    update_participant_response = await client.patch(
        f'/api/v1/rooms/{room["id"]}/participants/{participant.user.id}',
        headers=owner.headers,
        json={'role': 'moderator'},
    )
    assert update_participant_response.status_code == status.HTTP_200_OK
    assert update_participant_response.json()['role'] == 'moderator'

    room_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}',
        headers=owner.headers,
        json={
            'title': 'Updated study room',
            'max_participants': 5,
        },
    )
    assert room_update_response.status_code == status.HTTP_200_OK
    assert room_update_response.json()['title'] == 'Updated study room'

    message_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/messages/',
        headers=owner.headers,
        json={'content': 'Hello from tests'},
    )
    assert message_response.status_code == status.HTTP_200_OK
    message = message_response.json()
    assert message['sender_username'] == owner.payload['username']

    messages_response = await client.get(
        f'/api/v1/rooms/{room["id"]}/messages/',
        headers=owner.headers,
    )
    assert messages_response.status_code == status.HTTP_200_OK
    assert messages_response.json()['info']['total'] == 1

    message_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}/messages/{message["id"]}',
        headers=owner.headers,
        json={'content': 'Edited message'},
    )
    assert message_update_response.status_code == status.HTTP_200_OK
    assert message_update_response.json()['is_edited'] is True

    element_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=owner.headers,
        json={
            'element_type': 'text',
            'data': {'text': 'Board note'},
            'is_anonymous': False,
        },
    )
    assert element_response.status_code == status.HTTP_200_OK
    element = element_response.json()
    assert element['author_id'] == str(owner.user.id)

    anonymous_element_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=owner.headers,
        json={
            'element_type': 'question',
            'data': {'text': 'Anonymous question'},
            'is_anonymous': True,
        },
    )
    assert anonymous_element_response.status_code == status.HTTP_200_OK
    assert anonymous_element_response.json()['author_id'] is None

    elements_response = await client.get(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=owner.headers,
    )
    assert elements_response.status_code == status.HTTP_200_OK
    assert elements_response.json()['info']['total'] == EXPECTED_BOARD_ELEMENTS

    element_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}',
        headers=owner.headers,
        json={
            'element_type': 'text',
            'data': {'text': 'Updated board note'},
            'is_anonymous': False,
        },
    )
    assert element_update_response.status_code == status.HTTP_200_OK

    comment_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}/comments/',
        headers=owner.headers,
        json={'content': 'Board comment', 'is_anonymous': True},
    )
    assert comment_response.status_code == status.HTTP_200_OK
    comment = comment_response.json()
    assert comment['author_id'] is None

    comments_response = await client.get(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}/comments/',
        headers=owner.headers,
    )
    assert comments_response.status_code == status.HTTP_200_OK
    assert comments_response.json()['info']['total'] == 1

    comment_update_response = await client.put(
        (
            f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}'
            f'/comments/{comment["id"]}'
        ),
        headers=owner.headers,
        json={'content': 'Updated comment', 'is_anonymous': False},
    )
    assert comment_update_response.status_code == status.HTTP_200_OK

    comment_delete_response = await client.delete(
        (
            f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}'
            f'/comments/{comment["id"]}'
        ),
        headers=owner.headers,
    )
    assert comment_delete_response.status_code == status.HTTP_200_OK
    assert comment_delete_response.json()['is_deleted'] is True

    pomodoro_response = await client.get(
        f'/api/v1/rooms/{room["id"]}/pomodoro/',
        headers=owner.headers,
    )
    assert pomodoro_response.status_code == status.HTTP_200_OK

    pomodoro_update_response = await client.patch(
        f'/api/v1/rooms/{room["id"]}/pomodoro/settings',
        headers=owner.headers,
        json={
            'work_duration': UPDATED_WORK_DURATION,
            'short_break_duration': 5,
            'long_break_duration': 15,
            'cycles_before_long': 4,
        },
    )
    assert pomodoro_update_response.status_code == status.HTTP_200_OK
    assert pomodoro_update_response.json()['work_duration'] == UPDATED_WORK_DURATION

    start_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/pomodoro/start',
        headers=owner.headers,
    )
    assert start_response.status_code == status.HTTP_200_OK
    assert start_response.json()['is_running'] is True

    pause_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/pomodoro/pause',
        headers=owner.headers,
    )
    assert pause_response.status_code == status.HTTP_200_OK
    assert pause_response.json()['is_running'] is False

    reset_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/pomodoro/reset',
        headers=owner.headers,
    )
    assert reset_response.status_code == status.HTTP_200_OK
    assert reset_response.json()['completed_cycles'] == 0

    message_delete_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/messages/{message["id"]}',
        headers=owner.headers,
    )
    assert message_delete_response.status_code == status.HTTP_200_OK

    element_delete_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}',
        headers=owner.headers,
    )
    assert element_delete_response.status_code == status.HTTP_200_OK
    assert element_delete_response.json()['is_deleted'] is True

    clear_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=owner.headers,
    )
    assert clear_response.status_code == status.HTTP_200_OK
    assert clear_response.json()['deleted_count'] >= 1

    remove_participant_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/participants/{participant.user.id}',
        headers=owner.headers,
    )
    assert remove_participant_response.status_code == status.HTTP_200_OK
    assert remove_participant_response.json()['left_at'] is not None

    end_room_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}',
        headers=owner.headers,
    )
    assert end_room_response.status_code == status.HTTP_200_OK
    assert end_room_response.json()['status'] == 'ended'


async def test_room_participant_cannot_manage_owner_resources(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
):
    owner = await register_verified_user(client, session_maker, user_payload)
    participant = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    project = await create_project(client, owner.headers)
    room = await create_room(client, owner.headers, project['id'])

    join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant.headers,
        json={'room_code': room['room_code']},
    )
    assert join_response.status_code == status.HTTP_200_OK

    message_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/messages/',
        headers=owner.headers,
        json={'content': 'Owner message'},
    )
    assert message_response.status_code == status.HTTP_200_OK
    message = message_response.json()

    forbidden_room_update = await client.put(
        f'/api/v1/rooms/{room["id"]}',
        headers=participant.headers,
        json={
            'title': 'participant update',
            'max_participants': 5,
        },
    )
    assert forbidden_room_update.status_code == status.HTTP_403_FORBIDDEN

    forbidden_participant_update = await client.patch(
        f'/api/v1/rooms/{room["id"]}/participants/{owner.user.id}',
        headers=participant.headers,
        json={'role': 'moderator'},
    )
    assert forbidden_participant_update.status_code == status.HTTP_403_FORBIDDEN

    forbidden_message_update = await client.put(
        f'/api/v1/rooms/{room["id"]}/messages/{message["id"]}',
        headers=participant.headers,
        json={'content': 'Edited by participant'},
    )
    assert forbidden_message_update.status_code == status.HTTP_403_FORBIDDEN

    forbidden_pomodoro_update = await client.patch(
        f'/api/v1/rooms/{room["id"]}/pomodoro/settings',
        headers=participant.headers,
        json={
            'work_duration': UPDATED_WORK_DURATION,
            'short_break_duration': 5,
            'long_break_duration': 15,
            'cycles_before_long': 4,
        },
    )
    assert forbidden_pomodoro_update.status_code == status.HTTP_403_FORBIDDEN


async def test_user_lookup_and_role_assignment_flow(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    admin_auth,
):
    auth = await register_verified_user(client, session_maker, user_payload)

    get_response = await client.get(
        f'/api/v1/users/{auth.user.id}',
        headers=admin_auth.headers,
    )
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()['email'] == user_payload['email']

    forbidden_response = await client.get(
        f'/api/v1/users/{auth.user.id}',
        headers=auth.headers,
    )
    assert forbidden_response.status_code == status.HTTP_200_OK

    forbidden_assign_response = await client.post(
        f'/api/v1/users/{auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=auth.headers,
    )
    assert forbidden_assign_response.status_code == status.HTTP_403_FORBIDDEN

    assign_response = await client.post(
        f'/api/v1/users/{auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=admin_auth.headers,
    )
    assert assign_response.status_code == status.HTTP_200_OK
    assert assign_response.json() == {'success': True}

    duplicate_assign_response = await client.post(
        f'/api/v1/users/{auth.user.id}/roles/{settings.rbac.admin_role}',
        headers=admin_auth.headers,
    )
    assert duplicate_assign_response.status_code == status.HTTP_200_OK
    assert duplicate_assign_response.json()['detail'] == 'Role already assigned'

    missing_user_response = await client.post(
        f'/api/v1/users/{admin_auth.user.id}/roles/missing-role',
        headers=admin_auth.headers,
    )
    assert missing_user_response.status_code == status.HTTP_404_NOT_FOUND

    missing_lookup_response = await client.get(
        f'/api/v1/users/{admin_auth.user.id}',
        headers=admin_auth.headers,
    )
    assert missing_lookup_response.status_code == status.HTTP_200_OK
