from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.domains.quotes.models import Quote, QuoteLineItem
from backend.app.domains.quotes.schemas import QuoteCreate, QuoteUpdate

class QuoteRepository:
    """
    Handles persistence logic for Quotes and line items.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, quote_id: int) -> Optional[Quote]:
        result = await self.db.execute(
            select(Quote)
            .where(Quote.id == quote_id)
            .options(
                selectinload(Quote.items)
                .selectinload(QuoteLineItem.product)
            )
        )
        return result.scalars().first()

    async def get_by_quote_number(self, quote_number: str) -> List[Quote]:
        """
        Retrieves all versions of a quote by its common number identifier.
        """
        result = await self.db.execute(
            select(Quote)
            .where(Quote.quote_number == quote_number)
            .order_by(Quote.version.desc())
            .options(selectinload(Quote.items))
        )
        return list(result.scalars().all())

    async def get_latest_version(self, quote_number: str) -> Optional[Quote]:
        result = await self.db.execute(
            select(Quote)
            .where(Quote.quote_number == quote_number)
            .order_by(Quote.version.desc())
            .options(selectinload(Quote.items))
            .limit(1)
        )
        return result.scalars().first()

    async def list_quotes(self, limit: int = 100, offset: int = 0) -> List[Quote]:
        result = await self.db.execute(
            select(Quote)
            .options(selectinload(Quote.items))
            .limit(limit)
            .offset(offset)
            .order_by(Quote.created_at.desc())
        )
        return list(result.scalars().all())

    async def generate_next_quote_number(self) -> str:
        """
        Generates a unique reference quote number sequence.
        """
        # Simulated sequence generation: get max ID and format
        result = await self.db.execute(select(func.max(Quote.id)))
        max_id = result.scalar() or 0
        return f"QT-{100000 + max_id + 1}"

    async def create(self, creator_id: int, schema: QuoteCreate, quote_number: str, version: int = 1, parent_id: Optional[int] = None) -> Quote:
        """
        Creates and persists a blank quote shell.
        """
        db_quote = Quote(
            quote_number=quote_number,
            version=version,
            customer_id=schema.customer_id,
            price_book_id=schema.price_book_id,
            external_opportunity_id=schema.external_opportunity_id,
            created_by_id=creator_id,
            parent_quote_id=parent_id
        )
        self.db.add(db_quote)
        await self.db.flush()
        return db_quote

    async def update(self, db_quote: Quote, schema: QuoteUpdate) -> Quote:
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_quote, field, value)
        self.db.add(db_quote)
        await self.db.flush()
        return db_quote

    async def add_line_item(self, quote_id: int, product_id: int, qty: int, unit_price: float, discount: float) -> QuoteLineItem:
        total = (unit_price * (1.0 - discount / 100.0)) * qty
        db_item = QuoteLineItem(
            quote_id=quote_id,
            product_id=product_id,
            quantity=qty,
            unit_price=unit_price,
            discount_percentage=discount,
            total_price=total
        )
        self.db.add(db_item)
        await self.db.flush()
        return db_item

    async def clear_line_items(self, quote_id: int) -> None:
        """
        Deletes all existing line items from a quote before rewriting.
        """
        from sqlalchemy import delete
        await self.db.execute(delete(QuoteLineItem).where(QuoteLineItem.quote_id == quote_id))
        await self.db.flush()
