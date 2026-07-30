# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import itertools
import json
import uuid
from dataclasses import dataclass
from typing import Any, Sequence

from sqlalchemy import DateTime, Dialect, ForeignKey, Integer, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import override

from antarest.core.persistence import Base
from antarest.core.serde.json import from_json
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.model import CommandDTO

metadata = Base.metadata


@dataclass(frozen=True)
class LineageVersions:
    """
    Carries the versioning information of all variant ancestors of a study.

    Attributes:
        versions: one tuple (study id, data version) for each ancestor excluding root and including self
    """

    versions: list[tuple[str, int]]

    def is_up_to_date_with(self, current_versions: "LineageVersions") -> bool:
        """
        Up to date if lineage has not changed and all versions are equal or greater than current versions
        """
        for self_study, current_study in itertools.zip_longest(self.versions, current_versions.versions):
            if self_study is None or current_study is None:
                return False
            self_study_id, self_study_version = self_study
            current_study_id, current_study_version = current_study
            if self_study_id != current_study_id:
                return False
            if self_study_version < current_study_version:
                return False
        return True

    def to_json(self) -> str:
        return json.dumps(self.versions)

    @classmethod
    def from_json(cls, json_repr: str) -> "LineageVersions":
        data = json.loads(json_repr)
        return cls.from_tuples(data)

    @classmethod
    def from_tuples(cls, data: Sequence[tuple[str, int]]) -> "LineageVersions":
        return cls(versions=list(data))


class LineageVersionsType(TypeDecorator[LineageVersions]):
    """
    Defines a type to store lineage versions as a JSON string [["study-id", 3], ...]
    """

    impl = String
    cache_ok = True

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> LineageVersions | None:
        return LineageVersions.from_json(value) if value is not None else None

    @override
    def process_bind_param(self, value: LineageVersions | None, dialect: Dialect) -> str | None:
        return value.to_json() if value is not None else None


class VariantStudySnapshot(Base):
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
    __mapper_args__ = {"polymorphic_identity": "variant_study_snapshot"}

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("variantstudy.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_executed_command: Mapped[str | None] = mapped_column(String(), nullable=True)
    lineage_versions: Mapped[LineageVersions] = mapped_column(LineageVersionsType())

    @override
    def __str__(self) -> str:
        return f"[Snapshot] id={self.id}, lineag_versions={self.lineage_versions}"


class CommandBlock(Base):
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
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id or str(uuid.uuid4()),
            "study_id": self.study_id,
            "index": self.index,
            "command": self.command,
            "version": self.version,
            "args": self.args,
            "study_version": self.study_version,
            "user_id": self.user_id,
            "updated_at": self.updated_at,
        }

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


class CommandsListVersion(Base):
    __tablename__ = "commands_list_version"

    variant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("variantstudy.id", ondelete="CASCADE"), primary_key=True
    )
    version: Mapped[int] = mapped_column(Integer)


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

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    generation_task: Mapped[str | None] = mapped_column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variantstudy",
    }
    snapshot: Mapped[VariantStudySnapshot | None] = relationship(
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
    commands_version = relationship(CommandsListVersion, uselist=False)

    @override
    def __str__(self) -> str:
        return super().__str__() + f", snapshot={self.snapshot}"
