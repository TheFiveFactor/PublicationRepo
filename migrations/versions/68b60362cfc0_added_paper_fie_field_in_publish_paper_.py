"""added paper_fie field in publish_paper model

Revision ID: 68b60362cfc0
Revises: 9c7e7f9e5ede
Create Date: 2022-02-25 07:23:06.520396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68b60362cfc0'
down_revision = '9c7e7f9e5ede'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('publish_paper', sa.Column('paper_file', sa.String(length=155), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('publish_paper', 'paper_file')
    # ### end Alembic commands ###
