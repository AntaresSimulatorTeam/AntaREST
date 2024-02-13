"""This code is implemented manually to populate the `tag` and `study_tag` tables using
    pre-existing patch data in `study_additional_data` table.

Revision ID: dae93f1d9110
Revises: 3c70366b10ea
Create Date: 2024-02-08 10:30:20.590919

"""
import itertools
import json
import secrets

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection

from antarest.study.css4_colors import COLOR_NAMES

# revision identifiers, used by Alembic.
revision = "dae93f1d9110"
down_revision = "3c70366b10ea"
branch_labels = None
depends_on = None


def upgrade():
    # ### This code is implemented manually to populate the `tag` and `study_tag` tables ###

    # create connexion to the db
    connexion: Connection = op.get_bind()

    # retrieve the tags and the study-tag pairs from the db
    study_tags = connexion.execute("SELECT study_id,patch FROM study_additional_data")
    tags_by_ids = {}
    for study_id, patch in study_tags:
        obj = json.loads(patch or "{}")
        tags = frozenset(obj.get("study", {}).get("tags", ()))
        tags_by_ids[study_id] = tags
    labels = set(itertools.chain.from_iterable(tags_by_ids.values()))
    tags = {label: secrets.choice(COLOR_NAMES) for label in labels}

    for label, color in tags.items():
        connexion.execute(
            sa.text("INSERT INTO tag (label, color) VALUES (:label, :color)"), {"label": label, "color": color}
        )

    # Create relationships between studies and tags in the `study_tag` table
    study_tag_data = {(study_id, label) for study_id, tags in tags_by_ids.items() for label in tags}
    for study_id, label in study_tag_data:
        connexion.execute(
            sa.text("INSERT INTO study_tag (study_id, tag_label) VALUES (:study_id, :tag_label)"),
            {"study_id": study_id, "tag_label": label},
        )


def downgrade():
    # ### Unfortunately there is no way to distinguish between the tags that have been added from additional data
    # and those that have will be added following the data migration, using the current database scheme. Thus, we may
    # perform no action in the downgrade and leave the `tag` and `study_tag` tables unchanged.###
    pass
