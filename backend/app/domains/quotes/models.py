import enum
from sqlalchemy import String, ForeignKey, Numeric, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime
from backend.app.core.database import Base

class QuoteStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SYNCED = "synced"

class Quote(Base):
    """
    Quote database model representing sales quotations.
    Maintains revision versions, financial aggregates, status lifecycle,
    and pointers to the originating account managers.
    """
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quote_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[QuoteStatus] = mapped_column(String(50), default=QuoteStatus.DRAFT, nullable=False)
    
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    margin_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    price_book_id: Mapped[Optional[int]] = mapped_column(ForeignKey("price_books.id"), nullable=True)
    
    # Salesforce Opportunity ID mapping
    external_opportunity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Salesforce Quote ID mapping
    external_crm_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    parent_quote_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True)

    items: Mapped[List["QuoteLineItem"]] = relationship(back_populates="quote", cascade="all, delete-orphan")

class QuoteLineItem(Base):
    """
    QuoteLineItem database model representing line configuration items.
    Saves negotiated rates, discounts, quantities, and cost configurations.
    """
    __tablename__ = "quote_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    quote: Mapped["Quote"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
