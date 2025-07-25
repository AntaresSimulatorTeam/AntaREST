"""update_datetime

Revision ID: dcbe7dbf500b
Revises: 63ed81e5ce6f
Create Date: 2021-11-17 16:10:35.914371

"""
from typing import Optional, Union

from alembic import op
from dateutil import tz
from sqlalchemy.engine import Connection
from sqlalchemy import text
from datetime import timezone, datetime, tzinfo

# revision identifiers, used by Alembic.
revision = "dcbe7dbf500b"
down_revision = "9846e90c2868"
branch_labels = None
depends_on = None


def convert_to_utc(data: Union[str, datetime]) -> Optional[str]:
    if data is not None:
        dt = data
        if isinstance(data, str):
            dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
        dt = dt.replace(tzinfo=tz.gettz())
        d1 = dt.utcfromtimestamp(dt.timestamp()).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        return d1
    return None


def convert_to_local(data: str) -> Optional[str]:
    if data is not None:
        dt = data
        if isinstance(data, str):
            dt = datetime.strptime(data, "%Y-%m-%d %H:%M:%S.%f")
        dt = dt.replace(tzinfo=timezone.utc)
        dt = datetime.fromtimestamp(dt.timestamp())
        d1 = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        return d1
    return None


def time_convert(
        connexion: Connection,
        table: str,
        completion_type: bool = False,
        to_utc: bool = False,
) -> None:

    if completion_type:
        column1 = "creation_date"
        column2 = "completion_date"
    else:
        column1 = "created_at"
        column2 = "updated_at"

    results = connexion.execute(
        text(f"SELECT id, {column1}, {column2} FROM {table}")
    )
    for row in results:
        row_id = row[0]  # Accès par index pour SQLAlchemy 2.0
        d1 = (
            convert_to_utc(data=row[1])
            if to_utc
            else convert_to_local(data=row[1])
        )
        d2 = (
            convert_to_utc(data=row[2])
            if to_utc
            else convert_to_local(data=row[2])
        )
        connexion.execute(
            text(
                f"UPDATE {table} SET {column1} = :c1, {column2} = :c2 WHERE id = :row_id"
            ),
            {"c1": d1, "c2": d2, "row_id": row_id}
        )


def migrate_datetime(upgrade_mode: bool = True) -> None:
    connexion: Connection = op.get_bind()
    # DATASET
    time_convert(
        connexion=connexion,
        table="dataset",
        completion_type=False,
        to_utc=upgrade_mode,
    )

    # STUDIES
    time_convert(
        connexion=connexion,
        table="study",
        completion_type=False,
        to_utc=upgrade_mode,
    )

    # VARIANT STUDY SNAPSHOT
    results = connexion.execute(
        text("SELECT id, created_at FROM variant_study_snapshot")
    )
    for row in results:
        row_id = row[0]  # Accès par index pour SQLAlchemy 2.0
        dt = (
            convert_to_utc(data=row[1])
            if upgrade_mode
            else convert_to_local(data=row[1])
        )
        connexion.execute(
            text(
                "UPDATE variant_study_snapshot SET created_at = :created_at WHERE id = :row_id"
            ),
            {"created_at": dt, "row_id": row_id}
        )


def upgrade():
    migrate_datetime(upgrade_mode=True)


def downgrade():
    migrate_datetime(upgrade_mode=False)