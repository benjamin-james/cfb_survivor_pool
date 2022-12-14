"""empty message

Revision ID: 47adfc6784c8
Revises: 0256c48d62dd
Create Date: 2022-08-08 02:08:14.011627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47adfc6784c8'
down_revision = '0256c48d62dd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pick',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team', sa.Integer(), nullable=False),
    sa.Column('game', sa.Integer(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.CheckConstraint('self.created < self.game.start_date', name='game_is_in_future'),
    sa.CheckConstraint('self.game.away_team = self.team OR self.game.home_team = self.team', name='team_matches'),
    sa.ForeignKeyConstraint(['game'], ['game.id'], ),
    sa.ForeignKeyConstraint(['team'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pick')
    # ### end Alembic commands ###
