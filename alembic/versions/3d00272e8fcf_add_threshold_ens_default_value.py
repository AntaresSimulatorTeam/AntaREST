"""add_threshold_ens_default_value

Revision ID: 3d00272e8fcf
Revises: c4d7a91e2b36
Create Date: 2026-11-23 14:24:52.782633

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '3d00272e8fcf'
down_revision = 'c4d7a91e2b36'
branch_labels = None
depends_on = None


# `threshold_ens` exists from study version 9.3 on (see `initialize_adequacy_patch_parameters`).
# `study.version` is stored as text ("930", "1020"): compare it as an integer, since "1020" < "930" as text.
MIN_STUDY_VERSION = 930
# Same default as AntaREST (`initialize_adequacy_patch_parameters`) and Antares Simulator (`defaultThresholdEns`).
DEFAULT_THRESHOLD_ENS = 0.0


def upgrade() -> None:
    # Study versions can be stored in compact or dotted form.
    op.execute(
        text(
            """
            UPDATE adequacy_patch_parameters
            SET threshold_ens = :default
            WHERE threshold_ens IS NULL
              AND study_data_id IN (
                  SELECT sd.study_data_id
                  FROM study_data sd
                  JOIN study s ON s.id = sd.study_id
                  WHERE s.version IN ('930', '9.3', '1020', '10.2', '1030', '10.3')
              )
            """
        ).bindparams(default=DEFAULT_THRESHOLD_ENS)
    )


def downgrade() -> None:
    # Nothing to undo: a backfilled 0.0 cannot be told apart from a value set by a user,
    # and the simulator already reads a missing `threshold-ens` as 0.0.
    pass