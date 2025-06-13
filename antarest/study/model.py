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

import dataclasses
import enum
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path, PurePath, PurePosixPath
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional, Tuple, TypeAlias, cast

from antares.study.version import StudyVersion
from pydantic import BeforeValidator, ConfigDict, Field, PlainSerializer, computed_field, field_validator
from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import relationship, validates  # type: ignore
from typing_extensions import override

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.core.serde import AntaresBaseModel
from antarest.login.model import Group, GroupDTO, Identity
from antarest.study.css4_colors import COLOR_NAMES

if TYPE_CHECKING:
    # avoid circular import
    from antarest.core.tasks.model import TaskJob

DEFAULT_WORKSPACE_NAME = "default"

NEW_DEFAULT_STUDY_VERSION: StudyVersion = StudyVersion.parse("9.2")
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
STUDY_VERSION_9_2 = NEW_DEFAULT_STUDY_VERSION

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
}


class StudyGroup(Base):  # type:ignore
    """
    A table to manage the many-to-many relationship between `Study` and `Group`

    Attributes:
        study_id: The ID of the study associated with the group.
        group_id: The IS of the group associated with the study.
    """

    __tablename__ = "group_metadata"
    __table_args__ = (PrimaryKeyConstraint("study_id", "group_id"),)

    group_id: str = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False)
    study_id: str = Column(String(36), ForeignKey("study.id", ondelete="CASCADE"), index=True, nullable=False)

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


class StudyTag(Base):  # type:ignore
    """
    A table to manage the many-to-many relationship between `Study` and `Tag`

    Attributes:
        study_id: The ID of the study associated with the tag.
        tag_label: The label of the tag associated with the study.
    """

    __tablename__ = "study_tag"
    __table_args__ = (PrimaryKeyConstraint("study_id", "tag_label"),)

    study_id: str = Column(String(36), ForeignKey("study.id", ondelete="CASCADE"), index=True, nullable=False)
    tag_label: str = Column(String(40), ForeignKey("tag.label", ondelete="CASCADE"), index=True, nullable=False)

    @override
    def __str__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        return f"[{cls_name}] study_id={self.study_id}, tag={self.tag}"

    @override
    def __repr__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        study_id = self.study_id
        tag = self.tag
        return f"{cls_name}({study_id=}, {tag=})"


class Tag(Base):  # type:ignore
    """
    Represents a tag in the database.

    This class is used to store tags associated with studies.

    Attributes:
        label: The label of the tag.
        color: The color code associated with the tag.
    """

    __tablename__ = "tag"

    label = Column(String(40), primary_key=True, index=True)
    color: str = Column(String(20), index=True, default=lambda: secrets.choice(COLOR_NAMES))

    studies: List["Study"] = relationship("Study", secondary=StudyTag.__table__, back_populates="tags")

    @override
    def __str__(self) -> str:  # pragma: no cover
        return cast(str, self.label)

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


class CommentsDto(AntaresBaseModel):
    comments: str


class StudyAdditionalData(Base):  # type:ignore
    """
    Study additional data
    """

    __tablename__ = "study_additional_data"

    study_id = Column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    author = Column(String(255), default="Unknown")
    horizon = Column(String)
    patch = Column(String(), index=True, nullable=True)

    @override
    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        if not isinstance(other, StudyAdditionalData):
            return False
        return bool(other.author == self.author and other.horizon == self.horizon and other.patch == self.patch)


class Study(Base):  # type: ignore
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
        parent_id: The ID of the parent study, if any. Only makes sense for variant studies.
        public_mode: Defines the actions any user logged in is allowed to take on the study.
        owner_id: The ID of the owner of the study.
        archived: Whether the study is archived or not. Most operations are not allowed on archived studies.
                  The actual implementation of study archival may depend on the type of study. Currently,
                  only managed raw studies may be archived.
    """

    __tablename__ = "study"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    name = Column(String(255), index=True)
    type = Column(String(50), index=True)
    version = Column(String(255), index=True)
    author = Column(String(255))
    created_at = Column(DateTime, index=True)
    updated_at = Column(DateTime, index=True)
    last_access = Column(DateTime)
    path = Column(String())
    folder = Column(String, nullable=True, index=True)
    parent_id = Column(String(36), ForeignKey("study.id", name="fk_study_study_id"), index=True)
    public_mode = Column(Enum(PublicMode), default=PublicMode.NONE)
    owner_id = Column(Integer, ForeignKey(Identity.id), nullable=True, index=True)
    archived = Column(Boolean(), default=False, index=True)

    tags: List[Tag] = relationship(Tag, secondary=StudyTag.__table__, back_populates="studies")
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=StudyGroup.__table__, cascade="")
    additional_data = relationship(
        StudyAdditionalData,
        uselist=False,
        cascade="all, delete, delete-orphan",
    )

    # Define a one-to-many relationship between `Study` and `TaskJob`.
    # If the Study is deleted, all attached TaskJob must be deleted in cascade.
    jobs: List["TaskJob"] = relationship("TaskJob", back_populates="study", cascade="all, delete, delete-orphan")

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
        )

    def to_json_summary(self) -> Any:
        return {"id": self.id, "name": self.name}

    @validates("folder")  # type: ignore
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

    id: str = Column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_status: StudyContentStatus = Column(Enum(StudyContentStatus))
    workspace: str = Column(String(255), default=DEFAULT_WORKSPACE_NAME, nullable=False, index=True)
    missing = Column(DateTime, nullable=True, index=True)

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


@dataclasses.dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: List[Group]


class NonStudyFolderDTO(AntaresBaseModel):
    """
    DTO used by the explorer to list directories that aren't studies directory, this will be usefull for the front
    so the user can navigate in the hierarchy
    """

    path: PurePosixPath
    workspace: str
    name: str
    has_children: bool = Field(
        alias="hasChildren",
    )  # true when has at least one non-study-folder children

    model_config = ConfigDict(populate_by_name=True)

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


class WorkspaceMetadata(AntaresBaseModel):
    """
    DTO used by the explorer to list all workspaces
    """

    name: str


class PatchStudy(AntaresBaseModel):
    scenario: Optional[str] = None
    doc: Optional[str] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    tags: List[str] = []


class Patch(AntaresBaseModel, extra="allow"):
    study: Optional[PatchStudy] = None


class OwnerInfo(AntaresBaseModel):
    id: Optional[int] = None
    name: str


class StudyMetadataDTO(AntaresBaseModel):
    id: str
    name: str
    version: StudyVersionInt
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


class StudySimSettingsDTO(AntaresBaseModel):
    general: Dict[str, Any]
    input: Dict[str, Any]
    output: Dict[str, Any]
    optimization: Dict[str, Any]
    otherPreferences: Dict[str, Any]
    advancedParameters: Dict[str, Any]
    seedsMersenneTwister: Dict[str, Any]
    playlist: Optional[List[int]] = None


class StudySimResultDTO(AntaresBaseModel):
    name: str
    type: str
    settings: StudySimSettingsDTO
    completionDate: str
    status: str
    archived: bool


class StudyDownloadType(enum.StrEnum):
    LINK = "LINK"
    DISTRICT = "DISTRICT"
    AREA = "AREA"


class StudyDownloadLevelDTO(enum.StrEnum):
    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"

    def inc_date(self, date: datetime) -> datetime:
        if self.value == StudyDownloadLevelDTO.ANNUAL:
            return date.replace(year=date.year + 1)
        elif self.value == StudyDownloadLevelDTO.MONTHLY:
            if date.month == 12:
                return date.replace(year=date.year + 1, month=1)
            else:
                return date.replace(month=date.month + 1)
        elif self.value == StudyDownloadLevelDTO.WEEKLY:
            return date + timedelta(days=7)
        elif self.value == StudyDownloadLevelDTO.DAILY:
            return date + timedelta(days=1)
        elif self.value == StudyDownloadLevelDTO.HOURLY:
            return date + timedelta(hours=1)
        else:
            raise ShouldNotHappenException()


class ExportFormat(enum.StrEnum):
    ZIP = "application/zip"
    TAR_GZ = "application/tar+gz"
    JSON = "application/json"

    @classmethod
    def from_dto(cls, accept_header: str) -> "ExportFormat":
        """
        Convert the "Accept" header to the corresponding content type.

        Args:
            accept_header: Value of the "Accept" header.

        Returns:
            The corresponding content type: ZIP, TAR_GZ or JSON.
            By default, JSON is returned if the format is not recognized.
            For instance, if the "Accept" header is "*/*", JSON is returned.
        """
        mapping = {
            "application/zip": ExportFormat.ZIP,
            "application/tar+gz": ExportFormat.TAR_GZ,
            "application/json": ExportFormat.JSON,
        }
        return mapping.get(accept_header, ExportFormat.JSON)

    @property
    def suffix(self) -> str:
        """
        Returns the file suffix associated with the format: ".zip", ".tar.gz" or ".json".
        """
        mapping = {
            ExportFormat.ZIP: ".zip",
            ExportFormat.TAR_GZ: ".tar.gz",
            ExportFormat.JSON: ".json",
        }
        return mapping[self]


class StudyDownloadDTO(AntaresBaseModel):
    """
    DTO used to download outputs
    """

    type: StudyDownloadType
    years: Optional[List[int]]
    level: StudyDownloadLevelDTO
    filterIn: Optional[str]
    filterOut: Optional[str]
    filter: Optional[List[str]]
    columns: Optional[List[str]]
    synthesis: bool = False
    includeClusters: bool = False


class MatrixIndex(AntaresBaseModel):
    start_date: str = ""
    steps: int = 8760
    first_week_size: int = 7
    level: StudyDownloadLevelDTO = StudyDownloadLevelDTO.HOURLY


class TimeSerie(AntaresBaseModel):
    name: str
    unit: str
    data: List[Optional[float]] = []


class TimeSeriesData(AntaresBaseModel):
    type: StudyDownloadType
    name: str
    data: Dict[str, List[TimeSerie]] = {}


class MatrixAggregationResultDTO(AntaresBaseModel):
    index: MatrixIndex
    data: List[TimeSeriesData]
    warnings: List[str]


class MatrixAggregationResult(AntaresBaseModel):
    index: MatrixIndex
    data: Dict[Tuple[StudyDownloadType, str], Dict[str, List[TimeSerie]]]
    warnings: List[str]

    def to_dto(self) -> MatrixAggregationResultDTO:
        return MatrixAggregationResultDTO.model_construct(
            index=self.index,
            data=[
                TimeSeriesData.model_construct(
                    type=key_type,
                    name=key_name,
                    data=self.data[(key_type, key_name)],
                )
                for key_type, key_name in self.data
            ],
            warnings=self.warnings,
        )


class ReferenceStudy(AntaresBaseModel):
    version: str
    template_name: str
