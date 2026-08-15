"""add_cost_price_and_currency_to_products

Revision ID: ac8b161887f7
Revises: fc0ed3d4368d
Create Date: 2026-08-15 13:46:56.049648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac8b161887f7'
down_revision: Union[str, None] = 'fc0ed3d4368d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('cost_price', sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column('products', sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'))


def downgrade() -> None:
    op.drop_column('products', 'currency')
    op.drop_column('products', 'cost_price')
