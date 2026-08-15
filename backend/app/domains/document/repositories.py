from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.document.models import QuoteDocument

class DocumentRepository:
    """
    Handles persistence logic for Generated Documents.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, doc_id: int) -> Optional[QuoteDocument]:
        result = await self.db.execute(select(QuoteDocument).where(QuoteDocument.id == doc_id))
        return result.scalars().first()

    async def list_for_quote(self, quote_id: int) -> List[QuoteDocument]:
        result = await self.db.execute(
            select(QuoteDocument)
            .where(QuoteDocument.quote_id == quote_id)
            .order_by(QuoteDocument.generated_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, quote_id: int, creator_id: int, file_path: str) -> QuoteDocument:
        db_doc = QuoteDocument(
            quote_id=quote_id,
            created_by_id=creator_id,
            file_path=file_path
        )
        self.db.add(db_doc)
        await self.db.flush()
        return db_doc
