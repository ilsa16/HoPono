"""add confirmation_token to bookings

Revision ID: e060f6e73672
Revises: 0815f8c795bf
Create Date: 2026-02-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = 'e060f6e73672'
down_revision = 'bae643dbf04a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confirmation_token', sa.String(length=36), nullable=True))

    # Backfill existing rows with unique UUIDs
    conn = op.get_bind()
    bookings = conn.execute(sa.text("SELECT id FROM bookings WHERE confirmation_token IS NULL"))
    for row in bookings:
        conn.execute(
            sa.text("UPDATE bookings SET confirmation_token = :token WHERE id = :id"),
            {"token": str(uuid.uuid4()), "id": row[0]},
        )

    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.alter_column('confirmation_token', nullable=False)
        batch_op.create_unique_constraint('uq_bookings_confirmation_token', ['confirmation_token'])


def downgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('uq_bookings_confirmation_token', type_='unique')
        batch_op.drop_column('confirmation_token')
