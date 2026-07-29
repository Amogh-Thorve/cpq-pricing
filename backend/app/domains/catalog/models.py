from sqlalchemy import String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from backend.app.core.database import Base

class Category(Base):
    """
    Category database model for classifying products.
    Supports hierarchial nesting with a parent_id pointer.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    products: Mapped[List["Product"]] = relationship(back_populates="category")

class Product(Base):
    """
    Product database model representing items or services for sale.
    Integrates reference keys to external CRM (Salesforce) products.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    
    # Salesforce Product2 ID mapping
    external_crm_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
    price_book_entries: Mapped[List["PriceBookEntry"]] = relationship(back_populates="product", cascade="all, delete-orphan")

class PriceBook(Base):
    """
    PriceBook database model defining localized or customer-specific pricing catalogs.
    """
    __tablename__ = "price_books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_standard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    entries: Mapped[List["PriceBookEntry"]] = relationship(back_populates="price_book", cascade="all, delete-orphan")

class PriceBookEntry(Base):
    """
    PriceBookEntry database model acting as an intersection table.
    Links a Product to a specific PriceBook and assigns a custom price.
    """
    __tablename__ = "price_book_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    price_book_id: Mapped[int] = mapped_column(ForeignKey("price_books.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    custom_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    price_book: Mapped["PriceBook"] = relationship(back_populates="entries")
    product: Mapped["Product"] = relationship(back_populates="price_book_entries")
