from pathlib import Path

from aiosmtplib.errors import SMTPException
from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from fastapi_mail.errors import (
    ConnectionErrors,
    EmptyMessagesList,
    PydanticClassRequired,
)
from jinja2 import TemplateError

from src.app.core.settings import settings
from src.app.schemas.email import EmailSendData
from src.app.utils.logger import logger


class EmailService:
    def __init__(self, background_tasks: BackgroundTasks):
        self._background_tasks = background_tasks
        self._fast_mail = FastMail(
            ConnectionConfig(
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
        )

    def send_email(self, email_data: EmailSendData) -> None:
        if settings.email.use_credentials and not settings.email.password:
            logger.warning(
                'Email notification was not sent to %s: SMTP password is not '
                'configured',
                email_data.email_to,
            )
            return

        message = MessageSchema(
            subject=email_data.subject,
            recipients=[email_data.email_to],
            template_body=email_data.body,
            subtype='html',
        )

        self._background_tasks.add_task(
            self._send_email_safely,
            message,
            email_data.template_name,
            email_data.email_to,
        )

    async def _send_email_safely(
        self,
        message: MessageSchema,
        template_name: str,
        email_to: str,
    ) -> None:
        try:
            await self._fast_mail.send_message(message, template_name)
        except (
            ConnectionErrors,
            EmptyMessagesList,
            PydanticClassRequired,
            SMTPException,
            TemplateError,
            ValueError,
        ) as error:
            logger.warning(
                'Email notification was not sent to %s: %s',
                email_to,
                error,
            )
