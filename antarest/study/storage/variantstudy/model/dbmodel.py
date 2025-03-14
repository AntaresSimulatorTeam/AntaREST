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

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde.json import from_json
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.model import CommandDTO


class VariantStudySnapshot(Base):
    """
    Variant Study Snapshot based entity implementation.
    """

    __tablename__ = "variant_study_snapshot"

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("variantstudy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime.date] = mapped_column(DateTime)
    last_executed_command: Mapped[Optional[str]] = mapped_column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }

    @override
    def __str__(self) -> str:
        return f"[Snapshot] id={self.id}, created_at={self.created_at}"


class CommandBlock(Base):
    """
    Command Block based entity implementation.
    """

    __tablename__ = "commandblock"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    study_id: Mapped[str] = mapped_column(String(36), ForeignKey("variantstudy.id", ondelete="CASCADE"))
    index: Mapped[int] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer)
    args: Mapped[str] = mapped_column(String())
    study_version: Mapped[str] = mapped_column(String(36))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)

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
    Study filesystem based entity implementation.
    """

    __tablename__ = "variantstudy"

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    generation_task: Mapped[Optional[str]] = mapped_column(String(), nullable=True)

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
