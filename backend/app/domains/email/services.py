from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.email.repositories import EmailRepository
from backend.app.domains.email.models import EmailLog
from backend.app.domains.email.schemas import SendEmailRequest
from backend.app.domains.document.repositories import DocumentRepository
from backend.app.core.exceptions import DomainValidationError, EntityNotFoundError

class EmailService:
    """
    Business service layer responsible for drafting and dispatching outbound emails.
    Links approved quote PDFs as attachments and records execution logs.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_repo = EmailRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def send_quote_email(self, request: SendEmailRequest) -> EmailLog:
        """
        Orchestrate email sending.
        1. Find generated PDF document for the quote.
        2. Format body text.
        3. Dispatch via SMTP (stub/mocked for development).
        4. Log results.
        """
        # Ensure at least one PDF is generated for this quote
        documents = await self.doc_repo.list_for_quote(request.quote_id)
        if not documents:
            raise DomainValidationError("Cannot email a quote before generating its PDF proposal document first.")

        # Resolve latest document attachment
        latest_doc = documents[0]

        # SMTP Mock Execution
        # Future logic: use aiosmtplib to construct MIME messages and send
        status = "sent"
        error_msg = None

        # Record log
        return await self.email_repo.create_log(
            quote_id=request.quote_id,
            recipient=request.recipient,
            subject=request.subject,
            status=status,
            error_message=error_msg
        )
