from slowapi import Limiter
from slowapi.util import get_remote_address

from src.app.core.settings import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit.default],
)
