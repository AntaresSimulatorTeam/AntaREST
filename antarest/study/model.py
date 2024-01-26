import dataclasses
import enum
import typing as t
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import (  # type: ignore
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
)
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.login.model import Group, GroupDTO, Identity

if t.TYPE_CHECKING:
    # avoid circular import
    from antarest.core.tasks.model import TaskJob

DEFAULT_WORKSPACE_NAME = "default"

groups_metadata = Table(
    "group_metadata",
    Base.metadata,
    Column("group_id", String(36), ForeignKey("groups.id")),
    Column("study_id", String(36), ForeignKey("study.id")),
)


class StudyTag(Base):  # type:ignore
    """
    A table to manage the many-to-many relationship between `Study` and `Tag`
    """

    __tablename__ = "study_tag"

    study_id = Column(String(36), ForeignKey("study.id"), index=True, nullable=False)
    tag = Column(String, ForeignKey("tag.label"), index=True, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("study_id", "tag"),)

    def __str__(self) -> str:
        return f"[Study-Tag-Pair] study_id={self.study_id}, tag={self.tag}"

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, StudyTag):
            return False
        return bool(other.study_id == self.study_id and other.tag == self.tag)


class Tag(Base):  # type:ignore
    """
    A table to store all tags
    """

    __tablename__ = "tag"

    label = Column(String, primary_key=True, index=True)

    def __str__(self) -> str:
        return f"[Tag]" f" label={self.label},"

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, Tag):
            return False
        return bool(other.label == self.label)


STUDY_REFERENCE_TEMPLATES: t.Dict[str, str] = {
    "600": "empty_study_613.zip",
    "610": "empty_study_613.zip",
    "640": "empty_study_613.zip",
    "700": "empty_study_700.zip",
    "710": "empty_study_710.zip",
    "720": "empty_study_720.zip",
    "800": "empty_study_803.zip",
    "810": "empty_study_810.zip",
    "820": "empty_study_820.zip",
    "830": "empty_study_830.zip",
    "840": "empty_study_840.zip",
    "850": "empty_study_850.zip",
    "860": "empty_study_860.zip",
}

NEW_DEFAULT_STUDY_VERSION: str = "860"


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CommentsDto(BaseModel):
    comments: str


class StudyAdditionalData(Base):  # type:ignore
    """
    Study additional data
    """

    __tablename__ = "study_additional_data"

    study_id = Column(
        String(36),
        ForeignKey("study.id"),
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
    tags = relationship(Tag, secondary=lambda: StudyTag.__table__, cascade="")
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=lambda: groups_metadata, cascade="")
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
        return (
            f"[Study]"
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
        ForeignKey("study.id"),
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


class PatchStudy(BaseModel):
    scenario: t.Optional[str] = None
    doc: t.Optional[str] = None
    status: t.Optional[str] = None
    comments: t.Optional[str] = None
    tags: t.List[str] = []


class PatchArea(BaseModel):
    country: t.Optional[str] = None
    tags: t.List[str] = []


class PatchCluster(BaseModel):
    type: t.Optional[str] = None
    code_oi: t.Optional[str] = None

    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            return "-".join(string.split("_"))


class PatchOutputs(BaseModel):
    reference: t.Optional[str] = None


class Patch(BaseModel):
    study: t.Optional[PatchStudy] = None
    areas: t.Optional[t.Dict[str, PatchArea]] = None
    thermal_clusters: t.Optional[t.Dict[str, PatchCluster]] = None
    outputs: t.Optional[PatchOutputs] = None


class OwnerInfo(BaseModel):
    id: t.Optional[int] = None
    name: str


class StudyMetadataDTO(BaseModel):
    id: str
    name: str
    version: int
    created: str
    updated: str
    type: str
    owner: OwnerInfo
    groups: t.List[GroupDTO]
    public_mode: PublicMode
    workspace: str
    managed: bool
    archived: bool
    horizon: t.Optional[str]
    scenario: t.Optional[str]
    status: t.Optional[str]
    doc: t.Optional[str]
    folder: t.Optional[str] = None
    tags: t.List[str] = []


class StudyMetadataPatchDTO(BaseModel):
    name: t.Optional[str] = None
    author: t.Optional[str] = None
    horizon: t.Optional[str] = None
    scenario: t.Optional[str] = None
    status: t.Optional[str] = None
    doc: t.Optional[str] = None
    tags: t.List[str] = []


class StudySimSettingsDTO(BaseModel):
    general: t.Dict[str, t.Any]
    input: t.Dict[str, t.Any]
    output: t.Dict[str, t.Any]
    optimization: t.Dict[str, t.Any]
    otherPreferences: t.Dict[str, t.Any]
    advancedParameters: t.Dict[str, t.Any]
    seedsMersenneTwister: t.Dict[str, t.Any]
    playlist: t.Optional[t.List[int]] = None


class StudySimResultDTO(BaseModel):
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

    @staticmethod
    def from_dto(data: str) -> "ExportFormat":
        if data == "application/zip":
            return ExportFormat.ZIP
        if data == "application/tar+gz":
            return ExportFormat.TAR_GZ
        return ExportFormat.JSON


class StudyDownloadDTO(BaseModel):
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


class MatrixIndex(BaseModel):
    start_date: str = ""
    steps: int = 8760
    first_week_size: int = 7
    level: StudyDownloadLevelDTO = StudyDownloadLevelDTO.HOURLY


class TimeSerie(BaseModel):
    name: str
    unit: str
    data: t.List[t.Optional[float]] = []


class TimeSeriesData(BaseModel):
    type: StudyDownloadType
    name: str
    data: t.Dict[str, t.List[TimeSerie]] = {}


class MatrixAggregationResultDTO(BaseModel):
    index: MatrixIndex
    data: t.List[TimeSeriesData]
    warnings: t.List[str]


class MatrixAggregationResult(BaseModel):
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


class ReferenceStudy(BaseModel):
    version: str
    template_name: str
