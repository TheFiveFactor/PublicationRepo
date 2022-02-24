"""departments and department_areas table constraints

Revision ID: 4d473d677a0a
Revises: 72bc749109bc
Create Date: 2022-02-24 20:57:09.807439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d473d677a0a'
down_revision = '72bc749109bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('department_areas', sa.Column('department_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'department_areas', 'department', ['department_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'department_areas', type_='foreignkey')
    op.drop_column('department_areas', 'department_id')
    # ### end Alembic commands ###
