from pydantic import BaseModel, EmailStr


class EmailSendData(BaseModel):
    email_to: EmailStr
    subject: str
    template_name: str
    body: dict
