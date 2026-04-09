PERMISSION_DESCRIPTIONS: dict[str, str] = {
    'users:read': 'Read user data',
    'projects:read': 'Read projects',
    'projects:write': 'Create and update projects',
    'tags:read': 'Read tags',
    'tags:write': 'Manage tags',
    'rooms:read': 'Read rooms',
    'rooms:write': 'Create, update and delete rooms',
    'participants:read': 'Read room participants',
    'participants:write': 'Manage room participants',
    'chat:read': 'Read room chat messages',
    'chat:write': 'Send, edit and delete messages',
    'board:read': 'Read board elements and comments',
    'board:write': 'Manage board elements and comments',
    'pomodoro:read': 'Read pomodoro state',
    'pomodoro:write': 'Control pomodoro timer',
}

INITIAL_ROLE_SCOPES: dict[str, list[str]] = {
    'public': [
        'users:read',
        'users:write'
        'projects:read',
        'projects:write',
        'tags:read',
        'tags:write',
        'rooms:read',
        'rooms:write',
        'participants:read',
        'participants:write',
        'chat:read',
        'chat:write',
        'board:read',
        'board:write',
        'pomodoro:read',
        'pomodoro:write',
    ],
}