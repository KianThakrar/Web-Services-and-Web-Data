"""normalize date fields and race uniqueness

Revision ID: a944ea204f65
Revises: 486dc7c82aae
Create Date: 2026-03-09 12:36:57.437213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a944ea204f65'
down_revision: Union[str, None] = '486dc7c82aae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("drivers", recreate="always") as batch_op:
            batch_op.alter_column(
                "date_of_birth",
                existing_type=sa.VARCHAR(length=20),
                type_=sa.Date(),
                existing_nullable=True,
            )
        with op.batch_alter_table("races", recreate="always") as batch_op:
            batch_op.alter_column(
                "date",
                existing_type=sa.VARCHAR(length=20),
                type_=sa.Date(),
                existing_nullable=True,
            )
            batch_op.create_unique_constraint("uq_races_season_round", ["season", "round"])
    else:
        op.alter_column(
            "drivers",
            "date_of_birth",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Date(),
            existing_nullable=True,
            postgresql_using="date_of_birth::date",
        )
        op.alter_column(
            "races",
            "date",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Date(),
            existing_nullable=True,
            postgresql_using="date::date",
        )
        op.create_unique_constraint("uq_races_season_round", "races", ["season", "round"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("races", recreate="always") as batch_op:
            batch_op.drop_constraint("uq_races_season_round", type_="unique")
            batch_op.alter_column(
                "date",
                existing_type=sa.Date(),
                type_=sa.VARCHAR(length=20),
                existing_nullable=True,
            )
        with op.batch_alter_table("drivers", recreate="always") as batch_op:
            batch_op.alter_column(
                "date_of_birth",
                existing_type=sa.Date(),
                type_=sa.VARCHAR(length=20),
                existing_nullable=True,
            )
    else:
        op.drop_constraint("uq_races_season_round", "races", type_="unique")
        op.alter_column(
            "races",
            "date",
            existing_type=sa.Date(),
            type_=sa.VARCHAR(length=20),
            existing_nullable=True,
            postgresql_using="date::text",
        )
        op.alter_column(
            "drivers",
            "date_of_birth",
            existing_type=sa.Date(),
            type_=sa.VARCHAR(length=20),
            existing_nullable=True,
            postgresql_using="date_of_birth::text",
        )
