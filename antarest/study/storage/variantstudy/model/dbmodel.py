# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import datetime
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde.json import from_json
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.model import CommandDTO


class VariantStudySnapshot(Base):  # type: ignore
    """
    Metadata about a variant snapshot.

    Attributes:
        id: the variant study ID.
        created_at: the timestamp at which the snapshot was generated.
        last_executed_command: the ID of the last command applied when the snapshot has been generated.
                               This information can be useful to not re-generate the snapshot from scratch
                               (starting from the parent study), when some commands are simply appended
                               to the list of commands.
    """

    __tablename__ = "variant_study_snapshot"

    id: str = Column(
        String(36),
        ForeignKey("variantstudy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: datetime.date = Column(DateTime)
    last_executed_command: Optional[str] = Column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }

    @override
    def __str__(self) -> str:
        return f"[Snapshot] id={self.id}, created_at={self.created_at}"


class CommandBlock(Base):  # type: ignore
    """
    Storage of commands in database.

    A command "block" can actually contain multiple commands of the same kind (for example several "create_cluster" commands).

    Attributes:
        id: An ID of this block of commands
        study_id: The ID of the variant study to which those commands belong.
        index: Needed to order the commands of a variant study.
        version: The version of the COMMAND (not the study). The serialization of commands to database may change from
                 one version of the application to another, we need to guarantee backwards compatibility when reading
                 old versions.
        args: JSON representation of the actual data of the command(s) (for example, the name of the cluster to create, etc).
        study_version: The version of the study to which those commands belong.
                       Having that information here allows to carry out some validation checks.
        user_id: Who created this command.
        updated_at: When this command was last updated.
    """

    __tablename__ = "commandblock"

    id: str = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    study_id: str = Column(String(36), ForeignKey("variantstudy.id", ondelete="CASCADE"))
    index: int = Column(Integer)
    command: str = Column(String(255))
    version: int = Column(Integer)
    args: str = Column(String())
    study_version: str = Column(String(36))
    user_id: int = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=True)
    updated_at: datetime.datetime = Column(DateTime, nullable=True)

    def to_dto(self) -> CommandDTO:
        # Database may lack a version number, defaulting to 1 if so.
        version = self.version or 1
        return CommandDTO(
            id=self.id,
            action=self.command,
            args=from_json(self.args),
            version=version,
            study_version=self.study_version,
            user_id=self.user_id,
            updated_at=self.updated_at,
        )

    @override
    def __str__(self) -> str:
        return (
            f"CommandBlock(id={self.id!r},"
            f" study_id={self.study_id!r},"
            f" index={self.index!r},"
            f" command={self.command!r},"
            f" version={self.version!r},"
            f" args={self.args!r})"
            f" study_version={self.study_version!r}"
            f" user_id={self.user_id!r}"
            f" updated_at={self.updated_at!r}"
        )


class VariantStudy(Study):
    """
    Variant study representation.

    A variant study is defined by a parent study and additional commands that represent the differences from this parent.
    The actual application of the commands on top of the parent study to generate files on disk is called a "snapshot
    generation". The resulting generated files on disk constitue a study in antares-simulator format
    and is called a "snapshot".

    Attributes:
        generation_task: The ID of a task currently generating a snapshot for this study, if one is ongoing.
                         Note that only one generation task at a time is allowed, to not have concurrent writes
                         to the snapshot.
        snapshot: Some metadata about the last generated snapshot for this study.
        commands: The list of commands that defined the differences between the parent study and this study.
    """

    __tablename__ = "variantstudy"

    id: str = Column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    generation_task: Optional[str] = Column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variantstudy",
    }
    snapshot = relationship(
        VariantStudySnapshot,
        uselist=False,
        cascade="all, delete, delete-orphan",
    )
    commands = relationship(
        CommandBlock,
        uselist=True,
        order_by="CommandBlock.index",
        cascade="all, delete, delete-orphan",
    )

    @override
    def __str__(self) -> str:
        return super().__str__() + f", snapshot={self.snapshot}"

    @property
    def snapshot_dir(self) -> Path:
        """Get the path of the snapshot directory."""
        return Path(self.path) / "snapshot"

    def is_snapshot_up_to_date(self) -> bool:
        """Check if the snapshot exists and is up-to-date."""
        return (
            (self.snapshot is not None)
            and (self.snapshot.created_at >= self.updated_at)
            and (self.snapshot_dir / "study.antares").is_file()
        )

    def has_snapshot(self) -> bool:
        """Check if the snapshot exists."""
        return (self.snapshot is not None) and (self.snapshot_dir / "study.antares").is_file()
