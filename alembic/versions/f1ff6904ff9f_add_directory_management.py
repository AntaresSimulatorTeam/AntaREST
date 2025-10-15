"""
Add directory management for studies

This migration creates the directory and directory_group tables to enable
hierarchical organization of studies in the managed workspace.

Revision ID: f1ff6904ff9f
Revises: fd73601a9075
Create Date: 2025-10-09
"""
import uuid
from pathlib import PurePosixPath
from typing import Dict

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import and_, column, select, table

# revision identifiers, used by Alembic.
revision = "f1ff6904ff9f"
down_revision = "d2942741ae68"
branch_labels = None
depends_on = None


def parse_folder_path(folder: str) -> tuple[str, ...]:
    """
    Parse a folder path into a tuple of directory names.

    Args:
        folder: A POSIX-style path like "project1/subfolder"

    Returns:
        A tuple of directory names: ("project1", "subfolder")
    """
    path = PurePosixPath(folder)
    return path.parts


def upgrade() -> None:
    """
    Create directory tables and migrate existing folder data.
    """
    # Step 1: Create directory table
    op.create_table(
        "directory",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["directory.id"], name="fk_directory_parent_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["identities.id"]),
    )

    # Create indexes
    op.create_index("ix_directory_parent_id", "directory", ["parent_id"])
    op.create_index("ix_directory_owner_id", "directory", ["owner_id"])

    # Step 2: Create directory_group junction table
    op.create_table(
        "directory_group",
        sa.Column("directory_id", sa.String(36), nullable=False),
        sa.Column("group_id", sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint("directory_id", "group_id"),
        sa.ForeignKeyConstraint(["directory_id"], ["directory.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_directory_group_directory_id", "directory_group", ["directory_id"])
    op.create_index("ix_directory_group_group_id", "directory_group", ["group_id"])

    # Step 3: Add directory_id column to study table
    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.add_column(sa.Column("directory_id", sa.String(36), nullable=True))
        batch_op.create_index("ix_study_directory_id", ["directory_id"])
        batch_op.create_foreign_key(
            "fk_study_directory_id",
            "directory",
            ["directory_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # Step 4: Data migration - Build directory tree from study.folder
    bind = op.get_bind()

    # Define table structures for SQLAlchemy Core
    type_string = sa.String(length=256)
    type_int = sa.Integer()

    study_table = table(
        "study",
        column("id", type_string),
        column("folder", type_string),
        column("owner_id", type_int),
        column("directory_id", type_string),
    )

    rawstudy_table = table(
        "rawstudy",
        column("id", type_string),
        column("workspace", type_string),
    )

    directory_table = table(
        "directory",
        column("id", type_string),
        column("name", type_string),
        column("parent_id", type_string),
        column("owner_id", type_int),
    )

    group_metadata_table = table(
        "group_metadata",
        column("study_id", type_string),
        column("group_id", type_string),
    )

    directory_group_table = table(
        "directory_group",
        column("directory_id", type_string),
        column("group_id", type_string),
    )

    # Cache for created directories: path -> directory_id
    directory_cache: Dict[str, str] = {}

    # Batch data to insert
    directories_to_insert = []
    directory_groups_to_insert = []
    studies_to_update = []

    # Get all studies with folder information
    stmt = (
        select(study_table.c.id, study_table.c.folder, study_table.c.owner_id)
        .select_from(
            study_table.join(rawstudy_table, study_table.c.id == rawstudy_table.c.id)
        )
        .where(
            and_(
                rawstudy_table.c.workspace == "default",
                study_table.c.folder.isnot(None),
                study_table.c.folder != "",
            )
        )
    )
    studies = bind.execute(stmt).fetchall()

    # First pass: build directory structure and collect groups
    for study_id, folder, owner_id in studies:
        path_parts = parse_folder_path(folder)

        # Skip the last part (which is the study UUID itself, not a directory)
        # Only create directories for the parent folders
        if len(path_parts) <= 1:
            # No parent directories, study is at root level
            continue

        directory_parts = path_parts[:-1]  # Exclude the last part (study UUID)
        current_path = ""
        parent_id = None
        final_dir_id = None

        # Create each directory in the path if it doesn't exist
        for dir_name in directory_parts:
            current_path = f"{current_path}/{dir_name}" if current_path else dir_name

            if current_path not in directory_cache:
                # Prepare new directory for insertion
                dir_id = str(uuid.uuid4())
                directories_to_insert.append({
                    "id": dir_id,
                    "name": dir_name,
                    "parent_id": parent_id,
                    "owner_id": owner_id,
                })

                # Copy groups from study to directory (only for leaf directory)
                if current_path == "/".join(directory_parts):
                    stmt = select(group_metadata_table.c.group_id).where(
                        group_metadata_table.c.study_id == study_id
                    )
                    groups = bind.execute(stmt).fetchall()

                    for (group_id,) in groups:
                        directory_groups_to_insert.append({
                            "directory_id": dir_id,
                            "group_id": group_id,
                        })

                directory_cache[current_path] = dir_id

            parent_id = directory_cache[current_path]
            final_dir_id = directory_cache[current_path]

        # Prepare study update
        if final_dir_id:
            studies_to_update.append({
                "study_id": study_id,
                "directory_id": final_dir_id,
            })

    # Bulk insert directories
    if directories_to_insert:
        bind.execute(directory_table.insert(), directories_to_insert)

    # Bulk insert directory_group associations
    if directory_groups_to_insert:
        bind.execute(directory_group_table.insert(), directory_groups_to_insert)

    # Bulk update studies
    if studies_to_update:
        for item in studies_to_update:
            stmt = (
                study_table.update()
                .where(study_table.c.id == item["study_id"])
                .values(directory_id=item["directory_id"])
            )
            bind.execute(stmt)


def downgrade() -> None:
    """
    Remove directory tables and restore folder-only organization.
    """
    # Step 1: Remove directory_id column from study
    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.drop_constraint("fk_study_directory_id", type_="foreignkey")
        batch_op.drop_index("ix_study_directory_id")
        batch_op.drop_column("directory_id")

    # Step 2: Drop directory_group table
    op.drop_table("directory_group")

    # Step 3: Drop directory table
    op.drop_table("directory")
