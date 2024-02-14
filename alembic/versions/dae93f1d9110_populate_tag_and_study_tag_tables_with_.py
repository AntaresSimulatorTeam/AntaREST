"""This code is implemented manually to populate the `tag` and `study_tag` tables using
    pre-existing patch data in `study_additional_data` table.

Revision ID: dae93f1d9110
Revises: 3c70366b10ea
Create Date: 2024-02-08 10:30:20.590919

"""
import collections
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
    """
    This code is implemented manually to populate the `tag` and `study_tag` tables.\n
    Four steps to proceed:
        - Retrieve study-tags pairs from patches in `study_additional_data`.
        - Delete all rows in `tag` and `study_tag`, as tag updates between revised 3c70366b10ea and this version,
          do modify the data in patches alongside the two previous tables.
        - Populate `tag` table using unique tag-labels and by randomly generating their associated colors.
        - Populate `study_tag` using study-tags pairs.
    """

    # create connexion to the db
    connexion: Connection = op.get_bind()

    # retrieve the tags and the study-tag pairs from the db
    study_tags = connexion.execute("SELECT study_id,patch FROM study_additional_data")
    tags_by_ids = {}
    for study_id, patch in study_tags:
        obj = json.loads(patch or "{}")
        study = obj.get("study") or {}
        tags = frozenset(study.get("tags") or ())
        tags_by_ids[study_id] = tags

    # delete rows in tables `tag` and `study_tag`
    connexion.execute("DELETE FROM study_tag")
    connexion.execute("DELETE FROM tag")

    # insert the tags in the `tag` table
    labels = set(itertools.chain.from_iterable(tags_by_ids.values()))
    bulk_tags = [{"label": label, "color": secrets.choice(COLOR_NAMES)} for label in labels]
    sql = sa.text("INSERT INTO tag (label, color) VALUES (:label, :color)")
    connexion.execute(sql, *bulk_tags)

    # Create relationships between studies and tags in the `study_tag` table
    bulk_study_tags = ({"study_id": id_, "tag_label": lbl} for id_, tags in tags_by_ids.items() for lbl in tags)
    sql = sa.text("INSERT INTO study_tag (study_id, tag_label) VALUES (:study_id, :tag_label)")
    connexion.execute(sql, *bulk_study_tags)


def downgrade() -> None:
    """
    This code is implemented manually to downgrade to revised version of the db (3c70366b10ea).
    Three steps to proceed:
        - Retrieve study-tags pairs from `study_tag` table.
        - Update patches study-tags in `study_additional_data` using these pairs.
        - Delete all rows from `tag` and `study_tag`.
    """
    # create a connection to the db
    connexion: Connection = op.get_bind()

    # Creating the `tags_by_ids` mapping from data in the `study_tags` table
    tags_by_ids = collections.defaultdict(set)
    study_tags = connexion.execute("SELECT study_id, tag_label FROM study_tag")
    for study_id, tag_label in study_tags:
        tags_by_ids[study_id].add(tag_label)

    # Then, we read objects from the `patch` field of the `study_additional_data` table
    objects_by_ids = {}
    study_tags = connexion.execute("SELECT study_id, patch FROM study_additional_data")
    for study_id, patch in study_tags:
        obj = json.loads(patch or "{}")
        obj["study"] = obj.get("study") or {}
        obj["study"]["tags"] = obj["study"].get("tags") or []
        obj["study"]["tags"] = sorted(tags_by_ids[study_id] | set(obj["study"]["tags"]))
        objects_by_ids[study_id] = obj

    # Updating objects in the `study_additional_data` table
    sql = sa.text("UPDATE study_additional_data SET patch = :patch WHERE study_id = :study_id")
    bulk_patches = [{"study_id": id_, "patch": json.dumps(obj)} for id_, obj in objects_by_ids.items()]
    connexion.execute(sql, *bulk_patches)

    # Deleting study_tags and tags
    connexion.execute("DELETE FROM study_tag")
    connexion.execute("DELETE FROM tag")
