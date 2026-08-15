import logging
from typing import Protocol

logger = logging.getLogger("auth_email_service")

class EmailService(Protocol):
    """
    Protocol definition for sending authentication emails.
    """
    async def send_password_reset_email(self, email: str, token: str) -> None:
        ...

class PlaceholderEmailService:
    """
    Placeholder service logging the password reset token/link.
    """
    async def send_password_reset_email(self, email: str, token: str) -> None:
        logger.info(f"[EMAIL] Password reset requested for user {email}. Reset token: {token}")
        print(f"DEBUG: Password reset sent to {email}. Token: {token}")
