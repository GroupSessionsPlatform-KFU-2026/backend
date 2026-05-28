from uuid import uuid4

from fastapi import status
from httpx import AsyncClient
from src.tests.utils import read_data, register_verified_user


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
    max_participants: int = 4,
) -> dict:
    payload = read_data('room_create.json')
    payload['project_id'] = project_id
    payload['max_participants'] = max_participants

    response = await client.post(
        '/api/v1/rooms/',
        headers=headers,
        json=payload,
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def test_project_and_tag_error_cases(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
    admin_auth,
):
    owner_auth = await register_verified_user(client, session_maker, user_payload)
    other_user_auth = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    project = await create_project(client, owner_auth.headers)
    missing_id = uuid4()

    owner_hidden_response = await client.get(
        f'/api/v1/projects/{project["id"]}',
        headers=other_user_auth.headers,
    )
    assert owner_hidden_response.status_code == status.HTTP_404_NOT_FOUND

    update_hidden_response = await client.put(
        f'/api/v1/projects/{project["id"]}',
        headers=other_user_auth.headers,
        json={'title': 'Forbidden update'},
    )
    assert update_hidden_response.status_code == status.HTTP_404_NOT_FOUND

    archive_hidden_response = await client.delete(
        f'/api/v1/projects/{project["id"]}',
        headers=other_user_auth.headers,
    )
    assert archive_hidden_response.status_code == status.HTTP_404_NOT_FOUND

    missing_project_response = await client.get(
        f'/api/v1/projects/{missing_id}',
        headers=owner_auth.headers,
    )
    assert missing_project_response.status_code == status.HTTP_404_NOT_FOUND

    assign_missing_tag_response = await client.post(
        f'/api/v1/projects/{project["id"]}/tags/{missing_id}',
        headers=owner_auth.headers,
    )
    assert assign_missing_tag_response.status_code == status.HTTP_404_NOT_FOUND

    tag_response = await client.post(
        '/api/v1/tags/',
        headers=admin_auth.headers,
        json={
            'name': 'error-case',
            'color': '#112233',
            'description': 'Tag for error tests',
        },
    )
    assert tag_response.status_code == status.HTTP_200_OK
    tag = tag_response.json()

    remove_missing_relation_response = await client.delete(
        f'/api/v1/projects/{project["id"]}/tags/{tag["id"]}',
        headers=owner_auth.headers,
    )
    assert remove_missing_relation_response.status_code == status.HTTP_404_NOT_FOUND

    other_project_tags_response = await client.get(
        f'/api/v1/projects/{project["id"]}/tags',
        headers=other_user_auth.headers,
    )
    assert other_project_tags_response.status_code == status.HTTP_404_NOT_FOUND


async def test_room_lifecycle_error_cases(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
):
    owner_auth = await register_verified_user(client, session_maker, user_payload)
    participant_auth = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    overflow_auth = await register_verified_user(
        client,
        session_maker,
        {
            'email': f'overflow-{uuid4().hex}@example.com',
            'username': f'overflow-{uuid4().hex}',
            'password': 'test-password-123',
        },
    )
    project = await create_project(client, owner_auth.headers)
    room = await create_room(
        client,
        owner_auth.headers,
        project['id'],
        max_participants=1,
    )

    missing_join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant_auth.headers,
        json={'room_code': 'MISSING'},
    )
    assert missing_join_response.status_code == status.HTTP_404_NOT_FOUND

    first_join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert first_join_response.status_code == status.HTTP_200_OK

    duplicate_join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert duplicate_join_response.status_code == status.HTTP_200_OK
    assert duplicate_join_response.json()['id'] == first_join_response.json()['id']

    overflow_join_response = await client.post(
        '/api/v1/rooms/join',
        headers=overflow_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert overflow_join_response.status_code == status.HTTP_409_CONFLICT

    participant_update_room_response = await client.put(
        f'/api/v1/rooms/{room["id"]}',
        headers=participant_auth.headers,
        json={'title': 'Forbidden room update', 'max_participants': 2},
    )
    assert participant_update_room_response.status_code == status.HTTP_403_FORBIDDEN

    participant_end_room_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}',
        headers=participant_auth.headers,
    )
    assert participant_end_room_response.status_code == status.HTTP_403_FORBIDDEN

    end_room_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}',
        headers=owner_auth.headers,
    )
    assert end_room_response.status_code == status.HTTP_200_OK

    update_ended_room_response = await client.put(
        f'/api/v1/rooms/{room["id"]}',
        headers=owner_auth.headers,
        json={'title': 'Ended room update', 'max_participants': 2},
    )
    assert update_ended_room_response.status_code == status.HTTP_409_CONFLICT

    end_ended_room_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}',
        headers=owner_auth.headers,
    )
    assert end_ended_room_response.status_code == status.HTTP_409_CONFLICT

    join_ended_room_response = await client.post(
        '/api/v1/rooms/join',
        headers=overflow_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert join_ended_room_response.status_code == status.HTTP_409_CONFLICT


async def test_chat_board_and_comment_error_cases(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
):
    owner_auth = await register_verified_user(client, session_maker, user_payload)
    participant_auth = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    project = await create_project(client, owner_auth.headers)
    room = await create_room(client, owner_auth.headers, project['id'])
    missing_id = uuid4()

    join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert join_response.status_code == status.HTTP_200_OK

    message_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/messages/',
        headers=owner_auth.headers,
        json={'content': 'Owner message'},
    )
    assert message_response.status_code == status.HTTP_200_OK
    message = message_response.json()

    participant_message_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}/messages/{message["id"]}',
        headers=participant_auth.headers,
        json={'content': 'Forbidden edit'},
    )
    assert participant_message_update_response.status_code == status.HTTP_403_FORBIDDEN

    missing_message_delete_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/messages/{missing_id}',
        headers=owner_auth.headers,
    )
    assert missing_message_delete_response.status_code == status.HTTP_404_NOT_FOUND

    element_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=owner_auth.headers,
        json={
            'element_type': 'text',
            'data': {'text': 'Owner note'},
            'is_anonymous': False,
        },
    )
    assert element_response.status_code == status.HTTP_200_OK
    element = element_response.json()

    participant_board_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}',
        headers=participant_auth.headers,
        json={
            'element_type': 'text',
            'data': {'text': 'Forbidden note update'},
            'is_anonymous': False,
        },
    )
    assert participant_board_update_response.status_code == status.HTTP_403_FORBIDDEN

    participant_clear_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/board-elements/',
        headers=participant_auth.headers,
    )
    assert participant_clear_response.status_code == status.HTTP_403_FORBIDDEN

    missing_element_update_response = await client.put(
        f'/api/v1/rooms/{room["id"]}/board-elements/{missing_id}',
        headers=owner_auth.headers,
        json={
            'element_type': 'text',
            'data': {'text': 'Missing element'},
            'is_anonymous': False,
        },
    )
    assert missing_element_update_response.status_code == status.HTTP_404_NOT_FOUND

    comment_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}/comments/',
        headers=owner_auth.headers,
        json={'content': 'Owner comment', 'is_anonymous': False},
    )
    assert comment_response.status_code == status.HTTP_200_OK
    comment = comment_response.json()

    participant_comment_delete_response = await client.delete(
        (
            f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}'
            f'/comments/{comment["id"]}'
        ),
        headers=participant_auth.headers,
    )
    assert participant_comment_delete_response.status_code == status.HTTP_403_FORBIDDEN

    missing_comment_update_response = await client.put(
        (
            f'/api/v1/rooms/{room["id"]}/board-elements/{element["id"]}'
            f'/comments/{missing_id}'
        ),
        headers=owner_auth.headers,
        json={'content': 'Missing comment', 'is_anonymous': False},
    )
    assert missing_comment_update_response.status_code == status.HTTP_404_NOT_FOUND

    missing_element_comment_response = await client.post(
        f'/api/v1/rooms/{room["id"]}/board-elements/{missing_id}/comments/',
        headers=owner_auth.headers,
        json={'content': 'Missing element comment', 'is_anonymous': False},
    )
    assert missing_element_comment_response.status_code == status.HTTP_404_NOT_FOUND


async def test_participant_and_pomodoro_error_cases(
    client: AsyncClient,
    session_maker,
    user_payload: dict[str, str],
    second_user_payload: dict[str, str],
):
    owner_auth = await register_verified_user(client, session_maker, user_payload)
    participant_auth = await register_verified_user(
        client,
        session_maker,
        second_user_payload,
    )
    project = await create_project(client, owner_auth.headers)
    room = await create_room(client, owner_auth.headers, project['id'])
    missing_id = uuid4()

    join_response = await client.post(
        '/api/v1/rooms/join',
        headers=participant_auth.headers,
        json={'room_code': room['room_code']},
    )
    assert join_response.status_code == status.HTTP_200_OK

    participant_update_response = await client.patch(
        f'/api/v1/rooms/{room["id"]}/participants/{participant_auth.user.id}',
        headers=participant_auth.headers,
        json={'role': 'moderator'},
    )
    assert participant_update_response.status_code == status.HTTP_403_FORBIDDEN

    missing_participant_update_response = await client.patch(
        f'/api/v1/rooms/{room["id"]}/participants/{missing_id}',
        headers=owner_auth.headers,
        json={'role': 'moderator'},
    )
    assert missing_participant_update_response.status_code == status.HTTP_404_NOT_FOUND

    missing_participant_remove_response = await client.delete(
        f'/api/v1/rooms/{room["id"]}/participants/{missing_id}',
        headers=owner_auth.headers,
    )
    assert missing_participant_remove_response.status_code == status.HTTP_404_NOT_FOUND

    participant_pomodoro_update_response = await client.patch(
        f'/api/v1/rooms/{room["id"]}/pomodoro/settings',
        headers=participant_auth.headers,
        json={
            'work_duration': 25,
            'short_break_duration': 5,
            'long_break_duration': 15,
            'cycles_before_long': 4,
        },
    )
    assert participant_pomodoro_update_response.status_code == status.HTTP_403_FORBIDDEN

    missing_room_pomodoro_response = await client.get(
        f'/api/v1/rooms/{missing_id}/pomodoro/',
        headers=owner_auth.headers,
    )
    assert missing_room_pomodoro_response.status_code == status.HTTP_404_NOT_FOUND
