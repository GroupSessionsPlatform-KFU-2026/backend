from pathlib import Path

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

from src.app.core.settings import settings
from src.app.schemas.email import EmailSendData

conf = ConnectionConfig(
    MAIL_USERNAME=settings.email.username,
    MAIL_PASSWORD=settings.email.password,
    MAIL_FROM=settings.email.from_email,
    MAIL_PORT=settings.email.port,
    MAIL_SERVER=settings.email.server,
    MAIL_FROM_NAME=settings.email.from_name,
    MAIL_STARTTLS=settings.email.starttls,
    MAIL_SSL_TLS=settings.email.ssl_tls,
    USE_CREDENTIALS=settings.email.use_credentials,
    VALIDATE_CERTS=settings.email.validate_certs,
    TEMPLATE_FOLDER=Path(settings.email.template_folder),
)

fast_mail = FastMail(conf)


class EmailService:
    def __init__(self, background_tasks: BackgroundTasks):
        self._background_tasks = background_tasks
        self._fast_mail = fast_mail

    def send_email(self, email_data: EmailSendData) -> None:
        message = MessageSchema(
            subject=email_data.subject,
            recipients=[email_data.email_to],
            template_body=email_data.body,
            subtype='html',
        )

        self._background_tasks.add_task(
            self._fast_mail.send_message,
            message,
            email_data.template_name,
        )
