from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.ai.schemas import (
    CustomerSummaryRequest, CustomerSummaryResponse,
    QuoteSummaryRequest, QuoteSummaryResponse,
    EmailDraftRequest, EmailDraftResponse,
    ProductRecommendationRequest, ProductRecommendationResponse
)
from backend.app.core.config import settings

class AIService:
    """
    Business service layer integrating with the Google Gemini API.
    Acts as the Enterprise Copilot supporting sales reps with summaries, drafts, and recommendations.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        # Future logic: initialize google-genai client
        # e.g., self.ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def summarize_customer(self, request: CustomerSummaryRequest) -> CustomerSummaryResponse:
        """
        Synthesizes a customer's history, industry, and previous purchase patterns
        into a brief sales digest.
        """
        # Placeholder summary text
        return CustomerSummaryResponse(
            customer_id=request.customer_id,
            summary_text="[AI Summary] This is a high-value customer in the Enterprise software sector with 3 active quotes.",
            key_metrics=["LTV: $150k", "Average discount: 12%"]
        )

    async def summarize_quote(self, request: QuoteSummaryRequest) -> QuoteSummaryResponse:
        """
        Summarizes a quote's bundles and explains margins/pricing variations.
        """
        return QuoteSummaryResponse(
            quote_id=request.quote_id,
            summary_text="[AI Summary] Quote consists of 5 SaaS licenses and 1 implementation bundle.",
            explanation="The average margin of 78% is healthy, driven by standard pricing on software lines."
        )

    async def draft_email(self, request: EmailDraftRequest) -> EmailDraftResponse:
        """
        Drafts a customized email to accompany the proposal PDF.
        """
        return EmailDraftResponse(
            quote_id=request.quote_id,
            subject="Proposal details from Enterprise Systems",
            body="Hello,\n\nPlease find attached the quote details for your review.\n\nBest regards,\nSales team"
        )

    async def recommend_products(self, request: ProductRecommendationRequest) -> ProductRecommendationResponse:
        """
        Provides cross-sell / up-sell suggestions based on historical purchase trends.
        """
        return ProductRecommendationResponse(
            recommended_product_ids=[],
            reasoning="Customer has active Cloud subscription; recommending premium support SLA package add-ons.",
        )
