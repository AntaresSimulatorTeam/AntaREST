# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import typing as t
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from antares.study.version import StudyVersion
from pydantic import field_serializer, field_validator
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
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.core.serialization import AntaresBaseModel
from antarest.login.model import Group, GroupDTO, Identity
from antarest.study.css4_colors import COLOR_NAMES

if t.TYPE_CHECKING:
    # avoid circular import
    from antarest.core.tasks.model import TaskJob

DEFAULT_WORKSPACE_NAME = "default"

NEW_DEFAULT_STUDY_VERSION: StudyVersion = StudyVersion.parse("8.8")
STUDY_VERSION_6_0 = StudyVersion.parse("6.0")
STUDY_VERSION_6_1 = StudyVersion.parse("6.1")
STUDY_VERSION_6_4 = StudyVersion.parse("6.4")
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
STUDY_VERSION_8_8 = NEW_DEFAULT_STUDY_VERSION
STUDY_VERSION_9_1 = StudyVersion.parse("9.1")
STUDY_VERSION_9_2 = StudyVersion.parse("9.2")

STUDY_REFERENCE_TEMPLATES: t.Mapping[StudyVersion, str] = {
    STUDY_VERSION_6_0: "empty_study_613.zip",
    STUDY_VERSION_6_1: "empty_study_613.zip",
    STUDY_VERSION_6_4: "empty_study_613.zip",
    STUDY_VERSION_7_0: "empty_study_700.zip",
    STUDY_VERSION_7_1: "empty_study_710.zip",
    STUDY_VERSION_7_2: "empty_study_720.zip",
    STUDY_VERSION_8: "empty_study_803.zip",
    STUDY_VERSION_8_1: "empty_study_810.zip",
    STUDY_VERSION_8_2: "empty_study_820.zip",
    STUDY_VERSION_8_3: "empty_study_830.zip",
    STUDY_VERSION_8_4: "empty_study_840.zip",
    STUDY_VERSION_8_5: "empty_study_850.zip",
    STUDY_VERSION_8_6: "empty_study_860.zip",
    STUDY_VERSION_8_7: "empty_study_870.zip",
    STUDY_VERSION_8_8: "empty_study_880.zip",
    STUDY_VERSION_9_2: "empty_study_920.zip",
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

    def __str__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        return f"[{cls_name}] study_id={self.study_id}, group={self.group_id}"

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

    def __str__(self) -> str:  # pragma: no cover
        cls_name = self.__class__.__name__
        return f"[{cls_name}] study_id={self.study_id}, tag={self.tag}"

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

    studies: t.List["Study"] = relationship("Study", secondary=StudyTag.__table__, back_populates="tags")

    def __str__(self) -> str:  # pragma: no cover
        return t.cast(str, self.label)

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

    def __eq__(self, other: t.Any) -> bool:
        if not super().__eq__(other):
            return False
        if not isinstance(other, StudyAdditionalData):
            return False
        return bool(other.author == self.author and other.horizon == self.horizon and other.patch == self.patch)


class Study(Base):  # type: ignore
    """
    Standard Study entity
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

    tags: t.List[Tag] = relationship(Tag, secondary=StudyTag.__table__, back_populates="studies")
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=StudyGroup.__table__, cascade="")
    additional_data = relationship(
        StudyAdditionalData,
        uselist=False,
        cascade="all, delete, delete-orphan",
    )

    # Define a one-to-many relationship between `Study` and `TaskJob`.
    # If the Study is deleted, all attached TaskJob must be deleted in cascade.
    jobs: t.List["TaskJob"] = relationship("TaskJob", back_populates="study", cascade="all, delete, delete-orphan")

    __mapper_args__ = {"polymorphic_identity": "study", "polymorphic_on": type}

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

    def __eq__(self, other: t.Any) -> bool:
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

    def to_json_summary(self) -> t.Any:
        return {"id": self.id, "name": self.name}


class RawStudy(Study):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "rawstudy"

    id = Column(
        String(36),
        ForeignKey("study.id", ondelete="CASCADE"),
        primary_key=True,
    )
    content_status = Column(Enum(StudyContentStatus))
    workspace = Column(String(255), default=DEFAULT_WORKSPACE_NAME, nullable=False, index=True)
    missing = Column(DateTime, nullable=True, index=True)

    __mapper_args__ = {
        "polymorphic_identity": "rawstudy",
    }

    def __eq__(self, other: t.Any) -> bool:
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


@dataclasses.dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: t.List[Group]


class PatchStudy(AntaresBaseModel):
    scenario: t.Optional[str] = None
    doc: t.Optional[str] = None
    status: t.Optional[str] = None
    comments: t.Optional[str] = None
    tags: t.List[str] = []


class PatchArea(AntaresBaseModel):
    country: t.Optional[str] = None
    tags: t.List[str] = []


class PatchCluster(AntaresBaseModel):
    type: t.Optional[str] = None
    code_oi: t.Optional[str] = None

    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            return "-".join(string.split("_"))


class PatchOutputs(AntaresBaseModel):
    reference: t.Optional[str] = None


class Patch(AntaresBaseModel):
    study: t.Optional[PatchStudy] = None
    areas: t.Optional[t.Dict[str, PatchArea]] = None
    thermal_clusters: t.Optional[t.Dict[str, PatchCluster]] = None
    outputs: t.Optional[PatchOutputs] = None


class OwnerInfo(AntaresBaseModel):
    id: t.Optional[int] = None
    name: str


class StudyMetadataDTO(AntaresBaseModel):
    id: str
    name: str
    version: StudyVersion
    created: str
    updated: str
    type: str
    owner: OwnerInfo
    groups: t.List[GroupDTO]
    public_mode: PublicMode
    workspace: str
    managed: bool
    archived: bool
    horizon: t.Optional[str] = None
    scenario: t.Optional[str] = None
    status: t.Optional[str] = None
    doc: t.Optional[str] = None
    folder: t.Optional[str] = None
    tags: t.List[str] = []

    @field_serializer("version")
    def serialize_version(self, version: StudyVersion) -> int:
        return version.__int__()

    @field_validator("horizon", mode="before")
    def transform_horizon_to_str(cls, val: t.Union[str, int, None]) -> t.Optional[str]:
        # horizon can be an int.
        return str(val) if val else val  # type: ignore

    @field_validator("version", mode="before")
    def _validate_version(cls, v: t.Any) -> StudyVersion:
        return StudyVersion.parse(v)


class StudyMetadataPatchDTO(AntaresBaseModel):
    name: t.Optional[str] = None
    author: t.Optional[str] = None
    horizon: t.Optional[str] = None
    scenario: t.Optional[str] = None
    status: t.Optional[str] = None
    doc: t.Optional[str] = None
    tags: t.List[str] = []

    @field_validator("tags", mode="before")
    def _normalize_tags(cls, v: t.List[str]) -> t.List[str]:
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
    general: t.Dict[str, t.Any]
    input: t.Dict[str, t.Any]
    output: t.Dict[str, t.Any]
    optimization: t.Dict[str, t.Any]
    otherPreferences: t.Dict[str, t.Any]
    advancedParameters: t.Dict[str, t.Any]
    seedsMersenneTwister: t.Dict[str, t.Any]
    playlist: t.Optional[t.List[int]] = None


class StudySimResultDTO(AntaresBaseModel):
    name: str
    type: str
    settings: StudySimSettingsDTO
    completionDate: str
    referenceStatus: bool
    synchronized: bool
    status: str
    archived: bool


class StudyDownloadType(str, enum.Enum):
    LINK = "LINK"
    DISTRICT = "DISTRICT"
    AREA = "AREA"


class StudyDownloadLevelDTO(str, enum.Enum):
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


class ExportFormat(str, enum.Enum):
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
    years: t.Optional[t.List[int]]
    level: StudyDownloadLevelDTO
    filterIn: t.Optional[str]
    filterOut: t.Optional[str]
    filter: t.Optional[t.List[str]]
    columns: t.Optional[t.List[str]]
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
    data: t.List[t.Optional[float]] = []


class TimeSeriesData(AntaresBaseModel):
    type: StudyDownloadType
    name: str
    data: t.Dict[str, t.List[TimeSerie]] = {}


class MatrixAggregationResultDTO(AntaresBaseModel):
    index: MatrixIndex
    data: t.List[TimeSeriesData]
    warnings: t.List[str]


class MatrixAggregationResult(AntaresBaseModel):
    index: MatrixIndex
    data: t.Dict[t.Tuple[StudyDownloadType, str], t.Dict[str, t.List[TimeSerie]]]
    warnings: t.List[str]

    def to_dto(self) -> MatrixAggregationResultDTO:
        return MatrixAggregationResultDTO.construct(
            index=self.index,
            data=[
                TimeSeriesData.construct(
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
