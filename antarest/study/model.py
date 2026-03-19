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

import dataclasses
import enum
import secrets
import uuid
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING, Annotated, Any, List, Optional, TypeAlias

import numpy as np
from antares.study.version import StudyVersion
from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    alias_generators,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from typing_extensions import override

from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray
from antarest.login.model import Group, GroupDTO, Identity
from antarest.study.css4_colors import COLOR_NAMES

if TYPE_CHECKING:
    # avoid circular import
    from antarest.core.tasks.model import TaskJob

DEFAULT_WORKSPACE_NAME = "default"

NEW_DEFAULT_STUDY_VERSION: StudyVersion = StudyVersion.parse("9.3")
STUDY_VERSION_6_5 = StudyVersion.parse("6.5")
STUDY_VERSION_7_0 = StudyVersion.parse("7.0")
STUDY_VERSION_7_1 = StudyVersion.parse("7.1")
STUDY_VERSION_7_2 = StudyVersion.parse("7.2")
STUDY_VERSION_8 = StudyVersion.parse("8.0")
STUDY_VERSION_8_1 = StudyVersion.parse("8.1")
STUDY_VERSION_8_2 = StudyVersion.parse("8.2")
STUDY_VERSION_8_3 = StudyVersion.parse("8.3")
STUDY_VERSION_8_4 = StudyVersion.parse("8.4")
STUDY_VERSION_8_5 = StudyVersion.parse("8.5")
STUDY_VERSION_8_6 = StudyVersion.parse("8.6")
STUDY_VERSION_8_7 = StudyVersion.parse("8.7")
STUDY_VERSION_8_8 = StudyVersion.parse("8.8")
STUDY_VERSION_9_0 = StudyVersion.parse("9.0")
STUDY_VERSION_9_1 = StudyVersion.parse("9.1")
STUDY_VERSION_9_2 = StudyVersion.parse("9.2")
STUDY_VERSION_9_3 = NEW_DEFAULT_STUDY_VERSION

StudyVersionStr: TypeAlias = Annotated[StudyVersion, BeforeValidator(StudyVersion.parse), PlainSerializer(str)]
StudyVersionInt: TypeAlias = Annotated[StudyVersion, BeforeValidator(StudyVersion.parse), PlainSerializer(int)]


STUDY_REFERENCE_TEMPLATES: set[StudyVersion] = {
    STUDY_VERSION_7_0,
    STUDY_VERSION_7_1,
    STUDY_VERSION_7_2,
    STUDY_VERSION_8,
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_2,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_7,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_2,
    STUDY_VERSION_9_3,
}


class StudyGroup(Base):
    """
    A table to manage the many-to-many relationship between `Study` and `Group`

    Attributes:
        study_id: The ID of the study associated with the group.
        group_id: The IS of the group associated with the study.
    """

    __tablename__ = "group_metadata"
    __table_args__ = (PrimaryKeyConstraint("study_id", "group_id"),)

    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    study_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study.id", ondelete="CASCADE"), index=True, nullable=False
    )

    @override
    def __str__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        return f"[{cls_name}] study_id={self.study_id}, group={self.group_id}"

    @override
    def __repr__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        study_id = self.study_id
        group_id = self.group_id
        return f"{cls_name}({study_id=}, {group_id=})"


class StudyTag(Base):
    """
    A table to manage the many-to-many relationship between `Study` and `Tag`

    Attributes:
        study_id: The ID of the study associated with the tag.
        tag_label: The label of the tag associated with the study.
    """

    __tablename__ = "study_tag"
    __table_args__ = (PrimaryKeyConstraint("study_id", "tag_label"),)

    study_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("study.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tag_label: Mapped[str] = mapped_column(
        String(40), ForeignKey("tag.label", ondelete="CASCADE"), index=True, nullable=False
    )

    @override
    def __str__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        return f"[{cls_name}] study_id={self.study_id}, tag={self.tag_label}"

    @override
    def __repr__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        study_id = self.study_id
        tag = self.tag_label
        return f"{cls_name}({study_id=}, {tag=})"


class Directory(Base):
    """
    Represents a logical directory for organizing studies in the managed workspace.

    Directories are stored in the database and provide a hierarchical organization
    for studies, independent of the physical filesystem structure.

    Attributes:
        id: The unique identifier of the directory (UUID).
        name: The non-qualified name of the directory (e.g., "project1").
        parent_id: The ID of the parent directory, or None for root directories.
    """

    __tablename__ = "directory"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("directory.id", name="fk_directory_parent_id"), nullable=True, index=True
    )

    # Relationships
    parent = relationship("Directory", remote_side=[id], uselist=False)

    @override
    def __repr__(self) -> str:
        return f'Directory(id="{self.id}", name="{self.name}", parent_id="{self.parent_id}")'

    def to_metadata(self) -> "DirectoryMetadata":
        """Convert this Directory entity to DirectoryMetadata DTO."""
        return DirectoryMetadata(
            id=self.id,
            name=self.name,
            parent_id=self.parent_id,
        )


class Tag(Base):
    """
    Represents a tag in the database.

    This class is used to store tags associated with studies.

    Attributes:
        label: The label of the tag.
        color: The color code associated with the tag.
    """

    __tablename__ = "tag"

    label: Mapped[str] = mapped_column(String(40), primary_key=True, index=True)
    color: Mapped[str] = mapped_column(String(20), index=True, default=lambda: secrets.choice(COLOR_NAMES))

    studies: Mapped[List["Study"]] = relationship("Study", secondary=StudyTag.__table__, back_populates="tags")

    @override
    def __str__(self) -> str:  # pragma: no cover
        return self.label

    @override
    def __repr__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        label = self.label
        color = self.color
        return f"{cls_name}({label=}, {color=})"


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class StorageMode(enum.StrEnum):
    """
    Storage mode for study data.
    """

    FILESYSTEM = "filesystem"
    DATABASE = "database"


class CommentsDto(AntaresBaseModel):
    comments: str


class Study(Base):
    """
    Base study entity to save main metadata, common for any type of study (raw, variant, managed or not)

    Attributes:
        id: The unique identifier of the study in the application. A UUID.
        name: The name of the study, will be used for display purpose or searching. Note that this is NOT
              a unique identifier. May contain any type of characters.
        version: The version of the study, for example "7.0". Currently, any format accepted by StudyVersion.parse i
                 considered valid: "8.8" or "880" for example.
        author: The author name. Note that it may be different from the owner, and even not be a user of the application.
        created_at: The timestamp when the study was created.
        updated_at: The timestamp when the study was last updated.
        last_access: The timestamp when the study was last accessed.
        path: The path to a study directory on the file system. Note that depending on the type of study, this may
              represent different things. In particular, this is generally speaking not a valid study for the simulator.
              (for example, variants will generate snapshots in "<path> / snapshot").
        folder: Where the study is located in the workspace, from the user point of view.
                Note that generally speaking, this will not correspond to a valid folder on disk, this is only a logical
                folder presented to the user, not the way we organize data internally.
                This field is kept for backward compatibility but will be progressively replaced by directory_id.
        directory_id: The ID of the directory containing this study. Only for managed studies.
        parent_id: The ID of the parent study, if any. Only makes sense for variant studies.
        public_mode: Defines the actions any user logged in is allowed to take on the study.
        owner_id: The ID of the owner of the study.
        archived: Whether the study is archived or not. Most operations are not allowed on archived studies.
                  The actual implementation of study archival may depend on the type of study. Currently,
                  only managed raw studies may be archived.
        storage_mode: The storage mode for study data. Either FILESYSTEM (traditional file-based storage)
                      or DATABASE. Defaults to FILESYSTEM.
    """

    __tablename__ = "study"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(50), index=True)
    version: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    editor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    horizon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_access: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    path: Mapped[str] = mapped_column(String())
    folder: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    directory_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("directory.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("study.id", name="fk_study_study_id"), nullable=True, index=True
    )
    public_mode: Mapped[PublicMode] = mapped_column(Enum(PublicMode), default=PublicMode.NONE)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey(Identity.id), nullable=True, index=True)
    archived: Mapped[bool] = mapped_column(Boolean(), default=False, index=True)
    storage_mode: Mapped[StorageMode] = mapped_column(
        Enum(StorageMode), default=StorageMode.FILESYSTEM, nullable=False, index=True
    )

    tags: Mapped[List[Tag]] = relationship(Tag, secondary=StudyTag.__table__, back_populates="studies")
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=StudyGroup.__table__, cascade="")
    directory = relationship("Directory", uselist=False)

    # Define a one-to-many relationship between `Study` and `TaskJob`.
    # If the Study is deleted, all attached TaskJob must be deleted in cascade.
    jobs: Mapped[List["TaskJob"]] = relationship(
        "TaskJob", back_populates="study", cascade="all, delete, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "study", "polymorphic_on": type}

    @override
    def __str__(self) -> str:
        cls = self.__class__.__name__
        return (
            f"[{cls}]"
            f" id={self.id},"
            f" type={self.type},"
            f" name={self.name},"
            f" version={self.version},"
            f" updated_at={self.updated_at},"
            f" last_access={self.last_access},"
            f" owner={self.owner},"
            f" groups={[str(u) + ',' for u in self.groups]}"
        )

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Study):
            return False
        return bool(
            other.id == self.id
            and other.name == self.name
            and other.type == self.type
            and other.version == self.version
            and other.created_at == self.created_at
            and other.updated_at == self.updated_at
            and other.path == self.path
            and other.parent_id == self.parent_id
            and other.public_mode == self.public_mode
            and other.owner_id == self.owner_id
            and other.archived == self.archived
            and other.storage_mode == self.storage_mode
        )

    def to_json_summary(self) -> Any:
        return {"id": self.id, "name": self.name}

    @validates("folder")
    def validate_folder(self, key: str, folder: Optional[str]) -> Optional[str]:
        """
        We want to store the path in posix format in the database, even on windows.
        """
        return normalize_path(folder)


def normalize_path(path: Optional[str]) -> Optional[str]:
    """
    Turns any path including a windows path (with \ separator) to a posix path (with / separator).
    """
    if not path:
        return path
    pure_path = PurePath(path)
    return pure_path.as_posix()


class RawStudy(Study):
    """
    Study filesystem based entity implementation.

    Attributes:
        content_status: A validity status of this study content.
        workspace: The workspace this study belongs to. Note that the workspace in particular defines
                   if the study is "managed" (if it belongs to the "default" workspace) or not.
        missing: A timestamp indicating when the study has been identified as missing on disk, typically by
                 a scan of the filesystem. When a study is missing, the deletion does not happen immediately,
                 in case there was a disk-mounting issue.
    """

    __tablename__ = "rawstudy"

    id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_status: Mapped[Optional[StudyContentStatus]] = mapped_column(Enum(StudyContentStatus), nullable=True)
    workspace: Mapped[str] = mapped_column(String(255), default=DEFAULT_WORKSPACE_NAME, nullable=False, index=True)
    missing: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "rawstudy",
    }

    @override
    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        if not isinstance(other, RawStudy):
            return False
        return bool(
            other.content_status == self.content_status
            and other.workspace == self.workspace
            and other.folder == self.folder
            and other.missing == self.missing
        )

    @override
    def __repr__(self) -> str:
        return (
            f'RawStudy(id="{self.id}", workspace="{self.workspace}", folder="{self.folder}", missing="{self.missing}")'
        )

    def to_enhanced_json_summary(self) -> Any:
        """
        Extend the JSON summary with folder and workspace details.
        Useful for delete events to help the frontend stay synchronized.
        """
        return {
            **super().to_json_summary(),
            "folder": self.folder,
            "workspace": self.workspace,
        }


class StudyDiskSpaceAnalysis(Base):
    """
    Study disk space analysis entity implementation
    """

    __tablename__ = "study_disk_space_analysis"

    study_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("study.id", name="fk_study_disk_space_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    disk_space: Mapped[int] = mapped_column(Integer, nullable=False)
    last_analysis_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    study: Mapped["Study"] = relationship("Study", uselist=False)


@dataclasses.dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: List[Group]


class FolderDTO(AntaresBaseModel):
    """
    DTO used by the explorer to list directories that aren't studies directory, this will be usefull for the front
    so the user can navigate in the hierarchy
    """

    path: PurePosixPath
    workspace: str
    name: str
    has_children: bool  # true when has at least one non-study-folder children
    is_study_folder: bool = Field(
        default=False,
    )  # true when this folder is a study folder, used to display the icon in the front
    model_config = ConfigDict(populate_by_name=True, alias_generator=alias_generators.to_camel)

    @computed_field(alias="parentPath")
    def parent_path(self) -> PurePosixPath:
        """
        This computed field is convenient for the front.

        This field is also aliased as parentPath to match the front-end naming convention.

        Returns: the parent path of the current directory. Starting with the workspace as a root directory (we want /workspafe/folder1/sub... and not workspace/folder1/fsub... ).
        """
        workspace_path = PurePosixPath(f"/{self.workspace}")
        full_path = workspace_path.joinpath(self.path)
        return full_path.parent

    @field_validator("path", mode="before")
    def to_posix(cls, path: Path) -> PurePosixPath:
        """
        Always convert path to posix path.
        """
        return PurePosixPath(path)


class WorkspaceDTO(AntaresBaseModel):
    """
    DTO used by the explorer to list all workspaces
    """

    name: str
    disk_name: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True, alias_generator=alias_generators.to_camel)


class OwnerInfo(AntaresBaseModel):
    id: Optional[int] = None
    name: str


class StudyMetadataDTO(AntaresBaseModel):
    id: str
    name: str
    version: StudyVersionInt
    author: Optional[str] = None
    editor: Optional[str] = None
    created: str
    updated: str
    type: str
    owner: OwnerInfo
    groups: List[GroupDTO]
    public_mode: PublicMode
    workspace: str
    managed: bool
    archived: bool
    horizon: Optional[str] = None
    folder: Optional[str] = None
    tags: List[str] = []
    directory_id: Optional[str] = None
    parent_id: Optional[str] = None

    @field_validator("horizon", mode="before")
    def transform_horizon_to_str(cls, val: str | int | None) -> Optional[str]:
        # horizon can be an int.
        return str(val) if val else val  # type: ignore


class StudyMetadataPatchDTO(AntaresBaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    horizon: Optional[str] = None
    tags: List[str] = []

    @field_validator("tags", mode="before")
    def _normalize_tags(cls, v: List[str]) -> List[str]:
        """Remove leading and trailing whitespaces, and replace consecutive whitespaces by a single one."""
        tags = []
        for tag in v:
            tag = " ".join(tag.split())
            if not tag:
                raise ValueError("Tag cannot be empty")
            elif len(tag) > 40:
                raise ValueError(f"Tag is too long: {tag!r}")
            tags.append(tag)
        return tags


class DeleteManyStudies(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    study_ids: List[str] = Field(..., description="List of study UUIDs to delete")
    with_variants: bool = Field(default=False, description="Whether to delete variant studies as well")


class StudyDownloadType(enum.StrEnum):
    LINK = "LINK"
    DISTRICT = "DISTRICT"
    AREA = "AREA"


class MatrixFrequency(StrEnum):
    """
    An enumeration of matrix frequencies.

    Each frequency corresponds to a specific time interval for a matrix's data.
    """

    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"


class StudyDownloadDTO(AntaresBaseModel, alias_generator=to_camel):
    """
    DTO used to download outputs
    """

    type: StudyDownloadType
    years: list[int] = []
    level: MatrixFrequency
    filter_in: Annotated[Optional[str], Field(deprecated=True, default=None)]  # We don't consider it
    filter_out: Annotated[Optional[str], Field(deprecated=True, default=None)]  # We don't consider it
    filter: list[str] = []
    columns: list[str] = []
    synthesis: Annotated[bool, Field(deprecated=True, default=False)]  # We always consider it's False
    include_clusters: bool = False

    @model_validator(mode="after")
    def check_coherence(self) -> "StudyDownloadDTO":
        if self.include_clusters and self.type == StudyDownloadType.LINK:
            raise ValueError("Cannot ask for cluster values for type link")
        return self


class MatrixIndex(AntaresBaseModel):
    start_date: str = ""
    steps: int = 8760
    first_week_size: int = 7
    level: MatrixFrequency = MatrixFrequency.HOURLY


class TimeSerie(AntaresBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, ser_json_inf_nan="constants")

    name: str
    unit: str
    data: NpArray = np.zeros(shape=(0,))


class TimeSeriesData(AntaresBaseModel):
    type: StudyDownloadType
    name: str
    data: dict[str, list[TimeSerie]] = {}


class MatrixAggregationResultDTO(AntaresBaseModel):
    index: MatrixIndex
    data: list[TimeSeriesData]


class DirectoryMetadata(AntaresBaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


def _validate_directory_name(name: str) -> str:
    """
    Validate directory name format.

    Args:
        name: The directory name to validate.

    Returns:
        The validated and stripped directory name.

    Raises:
        ValueError: If the name is empty or contains path separators.
    """
    name = name.strip()
    if not name:
        raise ValueError("Directory name cannot be empty")
    if "/" in name or "\\" in name:
        raise ValueError("Directory name cannot contain path separators (/ or \\)")
    return name


class DirectoryCreation(AntaresBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate directory name."""
        return _validate_directory_name(v)


class DirectoryUpdate(AntaresBaseModel):
    """
    - **name**: New name for the directory (optional)
    - **parentId**: New parent directory ID (optional, empty string for root)
    """

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    parent_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate directory name."""
        return _validate_directory_name(v) if v is not None else v
