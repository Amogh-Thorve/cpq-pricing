from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.quotes.repositories import QuoteRepository
from backend.app.domains.quotes.models import Quote, QuoteStatus
from backend.app.domains.quotes.schemas import QuoteCreate, QuoteUpdate, QuoteLineItemCreate
from backend.app.domains.pricing.services import PricingService
from backend.app.domains.pricing.schemas import CalculatePriceRequest
from backend.app.domains.configuration.services import ConfigurationService
from backend.app.domains.configuration.schemas import ValidateConfigurationRequest
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError

class QuoteService:
    """
    Business service layer managing quote lifecycles.
    Coordinates pricing engine evaluations, bundle validations, and revisions version logs.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.quote_repo = QuoteRepository(db)
        self.pricing_service = PricingService(db)
        self.config_service = ConfigurationService(db)

    async def create_quote(self, creator_id: int, schema: QuoteCreate) -> Quote:
        """
        Creates a new quote.
        1. Validate configuration compatibility rules.
        2. Resolve pricing rules for each line item.
        3. Persist the quote and aggregate sums.
        """
        # Step 1: Validate bundle configuration compatibility
        product_ids = [item.product_id for item in schema.items]
        validation_res = await self.config_service.validate_selected_products(
            ValidateConfigurationRequest(product_ids=product_ids)
        )
        if not validation_res.is_valid:
            # Join validation messages to show reps why configuration failed
            messages = [e.message for e in validation_res.errors]
            raise DomainValidationError(f"Invalid quote configuration bundle: {'; '.join(messages)}")

        # Step 2: Create initial database quote shell
        quote_number = await self.quote_repo.generate_next_quote_number()
        quote = await self.quote_repo.create(
            creator_id=creator_id,
            schema=schema,
            quote_number=quote_number,
            version=1
        )

        # Step 3: Populate line items and apply Pricing Engine calculations
        total_amount = 0.0
        total_discount = 0.0
        total_margins = 0.0

        for item in schema.items:
            price_resp = await self.pricing_service.calculate_line_item_price(
                CalculatePriceRequest(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    customer_id=schema.customer_id,
                    price_book_id=schema.price_book_id,
                    requested_discount=item.discount_percentage
                )
            )

            await self.quote_repo.add_line_item(
                quote_id=quote.id,
                product_id=item.product_id,
                qty=item.quantity,
                unit_price=price_resp.base_price,
                discount=item.discount_percentage
            )

            total_amount += price_resp.total_amount
            total_discount += (price_resp.base_price - price_resp.discounted_price) * item.quantity
            total_margins += price_resp.margin_percentage

        # Step 4: Save aggregate sums
        quote.total_amount = total_amount
        quote.discount_amount = total_discount
        quote.margin_percentage = total_margins / max(1, len(schema.items))
        self.db.add(quote)

        return quote

    async def get_quote(self, quote_id: int) -> Quote:
        quote = await self.quote_repo.get_by_id(quote_id)
        if not quote:
            raise EntityNotFoundError(f"Quote with ID {quote_id} not found.")
        return quote

    async def list_quotes(self, limit: int = 100, offset: int = 0) -> List[Quote]:
        return await self.quote_repo.list_quotes(limit, offset)

    async def revise_quote(self, quote_id: int) -> Quote:
        """
        Creates a new version (revision) of an existing quote.
        Clones properties, increments version count, sets status back to DRAFT,
        and links to the parent quote ID for history audits.
        """
        parent_quote = await self.get_quote(quote_id)
        if parent_quote.status == QuoteStatus.SYNCED:
            raise DomainValidationError("Cannot revise a quote that has already been synced to CRM.")

        # Step 1: Create a clone shell
        next_version = parent_quote.version + 1
        
        # Build QuoteCreate mock schema from parent parameters
        schema = QuoteCreate(
            customer_id=parent_quote.customer_id,
            price_book_id=parent_quote.price_book_id,
            external_opportunity_id=parent_quote.external_opportunity_id,
            items=[]
        )
        
        new_quote = await self.quote_repo.create(
            creator_id=parent_quote.created_by_id,
            schema=schema,
            quote_number=parent_quote.quote_number,
            version=next_version,
            parent_id=parent_quote.id
        )

        # Step 2: Clone line items
        for item in parent_quote.items:
            await self.quote_repo.add_line_item(
                quote_id=new_quote.id,
                product_id=item.product_id,
                qty=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount_percentage
            )

        new_quote.total_amount = parent_quote.total_amount
        new_quote.discount_amount = parent_quote.discount_amount
        new_quote.margin_percentage = parent_quote.margin_percentage
        self.db.add(new_quote)

        return new_quote
