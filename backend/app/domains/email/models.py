from sqlalchemy import String, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from backend.app.core.database import Base

class EmailLog(Base):
    """
    EmailLog database model.
    Audits outbound proposal emails sent to client contacts.
    """
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # sent, failed
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
