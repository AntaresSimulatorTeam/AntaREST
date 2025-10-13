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
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "f1ff6904ff9f"
down_revision = "d2942741ae68"
branch_labels = None
depends_on = None


def parse_folder_path(folder: Optional[str]) -> List[str]:
    """
    Parse a folder path into a list of directory names.

    Args:
        folder: A POSIX-style path like "project1/subfolder"

    Returns:
        A list of directory names: ["project1", "subfolder"]
    """
    if not folder:
        return []
    path = PurePosixPath(folder)
    return list(path.parts)


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

    dialect_name: str = op.get_context().dialect.name
    if dialect_name == "postgresql":
        with op.batch_alter_table("study", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_study_directory_id",
                "directory",
                ["directory_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # Step 4: Data migration - Build directory tree from study.folder
    connection: Connection = op.get_bind()

    # Cache for created directories: path -> directory_id
    directory_cache: Dict[str, str] = {}

    # Get all studies with folder information
    studies = connection.execute(
        text("""
            SELECT s.id, s.folder, s.owner_id
            FROM study s
            JOIN rawstudy r ON s.id = r.id
            WHERE r.workspace = 'default' AND s.folder IS NOT NULL AND s.folder != ''
        """)
    ).fetchall()

    for study_id, folder, owner_id in studies:
        if not folder:
            continue

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
                # Create new directory
                dir_id = str(uuid.uuid4())
                connection.execute(
                    text("""
                        INSERT INTO directory (id, name, parent_id, owner_id)
                        VALUES (:id, :name, :parent_id, :owner_id)
                    """),
                    {
                        "id": dir_id,
                        "name": dir_name,
                        "parent_id": parent_id,
                        "owner_id": owner_id,
                    },
                )

                # Copy groups from study to directory (only for leaf directory)
                if current_path == "/".join(directory_parts):
                    groups = connection.execute(
                        text("SELECT group_id FROM group_metadata WHERE study_id = :study_id"),
                        {"study_id": study_id},
                    ).fetchall()

                    for (group_id,) in groups:
                        # Check if the association doesn't already exist
                        existing = connection.execute(
                            text("""
                                SELECT 1 FROM directory_group
                                WHERE directory_id = :dir_id AND group_id = :group_id
                            """),
                            {"dir_id": dir_id, "group_id": group_id},
                        ).fetchone()

                        if not existing:
                            connection.execute(
                                text("""
                                    INSERT INTO directory_group (directory_id, group_id)
                                    VALUES (:dir_id, :group_id)
                                """),
                                {"dir_id": dir_id, "group_id": group_id},
                            )

                directory_cache[current_path] = dir_id

            parent_id = directory_cache[current_path]
            final_dir_id = directory_cache[current_path]

        # Link study to its parent directory (not to itself!)
        if final_dir_id:
            connection.execute(
                text("UPDATE study SET directory_id = :dir_id WHERE id = :study_id"),
                {"dir_id": final_dir_id, "study_id": study_id},
            )


def downgrade() -> None:
    """
    Remove directory tables and restore folder-only organization.
    """
    # Step 1: Remove directory_id column from study
    dialect_name: str = op.get_context().dialect.name
    if dialect_name == "postgresql":
        with op.batch_alter_table("study", schema=None) as batch_op:
            batch_op.drop_constraint("fk_study_directory_id", type_="foreignkey")

    with op.batch_alter_table("study", schema=None) as batch_op:
        batch_op.drop_index("ix_study_directory_id")
        batch_op.drop_column("directory_id")

    # Step 2: Drop directory_group table
    op.drop_index("ix_directory_group_group_id", table_name="directory_group")
    op.drop_index("ix_directory_group_directory_id", table_name="directory_group")
    op.drop_table("directory_group")

    # Step 3: Drop directory table
    op.drop_index("ix_directory_owner_id", table_name="directory")
    op.drop_index("ix_directory_parent_id", table_name="directory")
    op.drop_table("directory")

    # Note: The folder column is preserved, so no data loss occurs
