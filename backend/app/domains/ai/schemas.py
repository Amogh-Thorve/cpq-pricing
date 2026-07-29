from pydantic import BaseModel
from typing import List, Optional

class CustomerSummaryRequest(BaseModel):
    customer_id: int

class CustomerSummaryResponse(BaseModel):
    customer_id: int
    summary_text: str
    key_metrics: List[str] = []

class QuoteSummaryRequest(BaseModel):
    quote_id: int

class QuoteSummaryResponse(BaseModel):
    quote_id: int
    summary_text: str
    explanation: str

class EmailDraftRequest(BaseModel):
    quote_id: int
    tone: str = "professional"

class EmailDraftResponse(BaseModel):
    quote_id: int
    subject: str
    body: str

class ProductRecommendationRequest(BaseModel):
    customer_id: int
    current_product_ids: List[int] = []

class ProductRecommendationResponse(BaseModel):
    recommended_product_ids: List[int] = []
    reasoning: str
