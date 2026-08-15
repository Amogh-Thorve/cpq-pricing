from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.document.repositories import DocumentRepository
from backend.app.domains.document.models import QuoteDocument
from backend.app.domains.document.schemas import GenerateDocumentRequest
from backend.app.domains.quotes.services import QuoteService
from backend.app.domains.quotes.models import QuoteStatus
from backend.app.core.exceptions import DomainValidationError

class DocumentService:
    """
    Business service layer responsible for dynamic PDF quote generation.
    Formats pricing, configuration, and terms into a client-facing catalog sheet.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.quote_service = QuoteService(db)

    async def generate_pdf(self, creator_id: int, request: GenerateDocumentRequest) -> QuoteDocument:
        """
        Orchestrate PDF document generation.
        1. Fetch quote details.
        2. Ensure the quote is approved/ready.
        3. Compile terms and layout into a PDF template.
        4. Save to files/ and record metadata.
        """
        quote = await self.quote_service.get_quote(request.quote_id)
        
        # In enterprise CPQ, quotes must be approved before generating official PDFs
        if quote.status not in (QuoteStatus.APPROVED, QuoteStatus.SYNCED):
            raise DomainValidationError("Cannot generate client-facing proposal documents for unapproved quotes.")

        # Simulated PDF file path creation:
        # Future logic: use ReportLab/Weasyprint to write HTML template to disk.
        file_path = f"static/documents/{quote.quote_number}_v{quote.version}.pdf"
        
        # Record file metadata in DB
        return await self.doc_repo.create(
            quote_id=request.quote_id,
            creator_id=creator_id,
            file_path=file_path
        )
