"""Add submitted flag to review response

Revision ID: e1f99a034c22
Revises: 347a14922cff
Create Date: 2020-11-10 22:21:01.794205

"""

# revision identifiers, used by Alembic.
revision = 'e1f99a034c22'
down_revision = '347a14922cff'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('review_response', sa.Column('is_submitted', sa.Boolean(), nullable=True))
    
    op.alter_column('review_response', 'submitted_timestamp',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)

    op.execute("""UPDATE review_response SET is_submitted=True, submitted_timestamp='2020-01-01'""")
    op.alter_column('review_response', 'is_submitted', nullable=False)

    op.execute("""update review_question set type='multi-file' where "order"=35""")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('review_response', 'submitted_timestamp',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.drop_column('review_response', 'is_submitted')
    # ### end Alembic commands ###
