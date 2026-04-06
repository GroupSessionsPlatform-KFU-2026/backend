from pydantic import BaseModel


class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class RegisterResponse(BaseModel):
    success: bool = True


class LogoutResponse(BaseModel):
    success: bool = True
