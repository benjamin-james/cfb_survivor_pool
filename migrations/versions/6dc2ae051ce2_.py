"""empty message

Revision ID: 6dc2ae051ce2
Revises: 3a24e3436e04
Create Date: 2022-08-14 04:34:51.972479

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dc2ae051ce2'
down_revision = '3a24e3436e04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entry', sa.Column('conference', sa.String(length=80), nullable=True))
    op.add_column('entry', sa.Column('year', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('entry', 'year')
    op.drop_column('entry', 'conference')
    # ### end Alembic commands ###
