"""Initial migration - create all CPQ platform tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-07-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # ------------------------------------------------------------------
    # customers
    # ------------------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("external_crm_id", sa.String(100), nullable=True, unique=True, index=True),
        sa.Column("account_manager_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
    )

    # ------------------------------------------------------------------
    # contacts
    # ------------------------------------------------------------------
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("external_crm_id", sa.String(100), nullable=True, unique=True, index=True),
    )

    # ------------------------------------------------------------------
    # categories
    # ------------------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
    )

    # ------------------------------------------------------------------
    # products
    # ------------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sku", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_crm_id", sa.String(100), nullable=True, unique=True, index=True),
    )

    # ------------------------------------------------------------------
    # price_books
    # ------------------------------------------------------------------
    op.create_table(
        "price_books",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_standard", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # ------------------------------------------------------------------
    # price_book_entries
    # ------------------------------------------------------------------
    op.create_table(
        "price_book_entries",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("price_book_id", sa.Integer(), sa.ForeignKey("price_books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("custom_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # ------------------------------------------------------------------
    # pricing_rules
    # ------------------------------------------------------------------
    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("conditions", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("actions", sa.JSON(), nullable=False, server_default="{}"),
    )

    # ------------------------------------------------------------------
    # configuration_rules
    # ------------------------------------------------------------------
    op.create_table(
        "configuration_rules",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
    )

    # ------------------------------------------------------------------
    # approval_policies
    # ------------------------------------------------------------------
    op.create_table(
        "approval_policies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("discount_threshold", sa.Numeric(5, 2), nullable=False),
        sa.Column("role_required", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    # ------------------------------------------------------------------
    # quotes
    # ------------------------------------------------------------------
    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("quote_number", sa.String(50), nullable=False, unique=True, index=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("margin_percentage", sa.Numeric(5, 2), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("price_book_id", sa.Integer(), sa.ForeignKey("price_books.id"), nullable=True),
        sa.Column("external_opportunity_id", sa.String(100), nullable=True),
        sa.Column("external_crm_id", sa.String(100), nullable=True),
        sa.Column("parent_quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True),
    )

    # ------------------------------------------------------------------
    # quote_line_items
    # ------------------------------------------------------------------
    op.create_table(
        "quote_line_items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
    )

    # ------------------------------------------------------------------
    # approval_requests
    # ------------------------------------------------------------------
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("policy_id", sa.Integer(), sa.ForeignKey("approval_policies.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("comments", sa.String(500), nullable=True),
        sa.Column("assigned_role", sa.String(50), nullable=False),
        sa.Column("decided_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
    )

    # ------------------------------------------------------------------
    # quote_documents
    # ------------------------------------------------------------------
    op.create_table(
        "quote_documents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
    )

    # ------------------------------------------------------------------
    # email_logs
    # ------------------------------------------------------------------
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("quote_id", sa.Integer(), sa.ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient", sa.String(255), nullable=False, index=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
    )

    # ------------------------------------------------------------------
    # integration_sync_logs
    # ------------------------------------------------------------------
    op.create_table(
        "integration_sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("integration_type", sa.String(50), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.String(500), nullable=True),
    )

    # ------------------------------------------------------------------
    # salesforce_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "salesforce_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("access_token", sa.String(500), nullable=False),
        sa.Column("refresh_token", sa.String(500), nullable=True),
        sa.Column("instance_url", sa.String(255), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_in", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("salesforce_tokens")
    op.drop_table("integration_sync_logs")
    op.drop_table("email_logs")
    op.drop_table("quote_documents")
    op.drop_table("approval_requests")
    op.drop_table("quote_line_items")
    op.drop_table("quotes")
    op.drop_table("approval_policies")
    op.drop_table("configuration_rules")
    op.drop_table("pricing_rules")
    op.drop_table("price_book_entries")
    op.drop_table("price_books")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("contacts")
    op.drop_table("customers")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
