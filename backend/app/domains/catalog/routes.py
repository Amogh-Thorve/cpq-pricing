from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.catalog.schemas import (
    ProductCreate, ProductRead, CategoryCreate, CategoryRead,
    PriceBookCreate, PriceBookRead, PriceBookEntryCreate, PriceBookEntryRead
)
from backend.app.domains.catalog.services import CatalogService

router = APIRouter(tags=["product-catalog"])

@router.get("/products", response_model=List[ProductRead])
async def list_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all products in catalog. Optionally filter by category.
    """
    service = CatalogService(db)
    return await service.list_products(limit=limit, offset=offset, category_id=category_id)

@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    schema: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Onboard a new product to the catalog (Admin/Sales representative only).
    """
    service = CatalogService(db)
    return await service.create_product(schema)

@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed catalog card for a product.
    """
    service = CatalogService(db)
    return await service.get_product(product_id)

@router.get("/categories", response_model=List[CategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List the structural categories tree.
    """
    service = CatalogService(db)
    return await service.list_categories()

@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    schema: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new product category taxonomy classification.
    """
    service = CatalogService(db)
    return await service.create_category(schema)

@router.get("/price-books", response_model=List[PriceBookRead])
async def list_price_books(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all price books.
    """
    service = CatalogService(db)
    return await service.price_book_repo.list()

@router.post("/price-books", response_model=PriceBookRead, status_code=status.HTTP_201_CREATED)
async def create_price_book(
    schema: PriceBookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Price Book catalog.
    """
    service = CatalogService(db)
    return await service.create_price_book(schema)

@router.post("/price-books/{price_book_id}/entries", response_model=PriceBookEntryRead, status_code=status.HTTP_201_CREATED)
async def add_price_book_entry(
    price_book_id: int,
    schema: PriceBookEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add or update a custom price mapping inside a Price Book.
    """
    service = CatalogService(db)
    return await service.add_price_book_entry(price_book_id, schema)
