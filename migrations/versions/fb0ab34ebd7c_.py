"""empty message

Revision ID: fb0ab34ebd7c
Revises: 7ce5c30d48c6
Create Date: 2017-08-16 08:28:45.222507

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fb0ab34ebd7c'
down_revision = '7ce5c30d48c6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'user', 'role', ['role_id'], ['id'])
    op.drop_column('user', 'role')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('role', mysql.VARCHAR(length=40), nullable=True))
    op.drop_constraint(None, 'user', type_='foreignkey')
    # ### end Alembic commands ###
