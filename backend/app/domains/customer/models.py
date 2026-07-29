from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from backend.app.core.database import Base

class Customer(Base):
    """
    Customer / Account database model representing client entities.
    Tracks CRM references, industry, and assigned account manager relationships.
    """
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Mapping to Salesforce Account ID
    external_crm_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    
    # Account Manager from User table
    account_manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    contacts: Mapped[List["Contact"]] = relationship(back_populates="customer", cascade="all, delete-orphan")

class Contact(Base):
    """
    Contact database model representing individual client stakeholders.
    Maps to Salesforce Contacts and belongs to a Customer account.
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Mapping to Salesforce Contact ID
    external_crm_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="contacts")
