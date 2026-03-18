class NotFoundError(Exception):
    message = 'Not Found'


class InternalServerError(Exception):
    message = 'Internal server error'


class ForbiddenError(Exception):
    message = 'Access denied'


class UnauthorizedError(Exception):
    message = 'You must be authorized'


class ConflictError(Exception):
    message = 'Conflict'