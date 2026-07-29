from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.catalog.repositories import ProductRepository, CategoryRepository, PriceBookRepository
from backend.app.domains.catalog.models import Product, Category, PriceBook, PriceBookEntry
from backend.app.domains.catalog.schemas import (
    ProductCreate, ProductUpdate,
    CategoryCreate, CategoryUpdate,
    PriceBookCreate, PriceBookUpdate, PriceBookEntryCreate
)
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError

class CatalogService:
    """
    Business service layer managing the product catalog, category categorization,
    and multiple price book definitions.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.price_book_repo = PriceBookRepository(db)

    async def create_product(self, schema: ProductCreate) -> Product:
        """
        Create a new product. SKU must be unique.
        """
        existing = await self.product_repo.get_by_sku(schema.sku)
        if existing:
            raise DomainValidationError(f"Product SKU '{schema.sku}' already exists.")
        
        if schema.category_id:
            category = await self.category_repo.get_by_id(schema.category_id)
            if not category:
                raise DomainValidationError(f"Category with ID {schema.category_id} does not exist.")
                
        return await self.product_repo.create(schema)

    async def get_product(self, product_id: int) -> Product:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found.")
        return product

    async def list_products(self, limit: int = 100, offset: int = 0, category_id: Optional[int] = None) -> List[Product]:
        return await self.product_repo.list(limit, offset, category_id)

    async def create_category(self, schema: CategoryCreate) -> Category:
        existing = await self.category_repo.get_by_name(schema.name)
        if existing:
            raise DomainValidationError(f"Category '{schema.name}' already exists.")
        return await self.category_repo.create(schema)

    async def list_categories(self) -> List[Category]:
        return await self.category_repo.list()

    async def create_price_book(self, schema: PriceBookCreate) -> PriceBook:
        """
        Create a new price book. If marked standard, disable other standard price books.
        """
        if schema.is_standard:
            existing_std = await self.price_book_repo.get_standard_price_book()
            if existing_std:
                # Toggle off the previous standard
                existing_std.is_standard = False
                self.db.add(existing_std)
                
        return await self.price_book_repo.create(schema)

    async def add_price_book_entry(self, price_book_id: int, schema: PriceBookEntryCreate) -> PriceBookEntry:
        # Verify both price book and product exist
        price_book = await self.price_book_repo.get_by_id(price_book_id)
        if not price_book:
            raise EntityNotFoundError(f"Price Book with ID {price_book_id} not found.")
            
        await self.get_product(schema.product_id)
        return await self.price_book_repo.add_entry(price_book_id, schema)

    async def get_product_price(self, product_id: int, price_book_id: Optional[int] = None) -> float:
        """
        Resolve the current unit price of a product.
        Checks custom price book first, falling back to standard price book,
        and finally the base product price.
        """
        product = await self.get_product(product_id)
        
        # 1. Check custom price book if specified
        if price_book_id:
            pb = await self.price_book_repo.get_by_id(price_book_id)
            if pb:
                for entry in pb.entries:
                    if entry.product_id == product_id and entry.is_active:
                        return entry.custom_price

        # 2. Check standard price book
        std_pb = await self.price_book_repo.get_standard_price_book()
        if std_pb:
            for entry in std_pb.entries:
                if entry.product_id == product_id and entry.is_active:
                    return entry.custom_price

        # 3. Fallback to base product list price
        return product.base_price
ClassSymbol = CatalogService
