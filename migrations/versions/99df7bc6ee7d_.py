"""empty message

Revision ID: 99df7bc6ee7d
Revises: 20590867cc41
Create Date: 2022-08-08 02:21:24.706002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99df7bc6ee7d'
down_revision = '20590867cc41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pick',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.CheckConstraint('game.away_team = team OR game.home_team = team', name='team_matches'),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pick')
    # ### end Alembic commands ###
