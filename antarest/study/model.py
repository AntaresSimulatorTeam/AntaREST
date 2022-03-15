import enum
import uuid
from dataclasses import dataclass
from datetime import timedelta, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey, Enum, Boolean  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.exceptions import ShouldNotHappenException
from antarest.core.model import PublicMode
from antarest.core.persistence import Base
from antarest.login.model import Group, Identity, GroupDTO

DEFAULT_WORKSPACE_NAME = "default"

groups_metadata = Table(
    "group_metadata",
    Base.metadata,
    Column("group_id", String(36), ForeignKey("groups.id")),
    Column("study_id", String(36), ForeignKey("study.id")),
)

STUDY_REFERENCE_TEMPLATES: Dict[str, str] = {
    "600": "empty_study_613.zip",
    "610": "empty_study_613.zip",
    "640": "empty_study_613.zip",
    "700": "empty_study_700.zip",
    "710": "empty_study_710.zip",
    "720": "empty_study_720.zip",
    "800": "empty_study_803.zip",
    "810": "empty_study_810.zip",
    "820": "empty_study_820.zip",
}

NEW_DEFAULT_STUDY_VERSION: str = "820"


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class CommentsDto(BaseModel):
    comments: str


@dataclass
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
    patch = Column(String(), nullable=True)

    def __eq__(self, other: Any) -> bool:
        if not super().__eq__(other):
            return False
        if not isinstance(other, StudyAdditionalData):
            return False
        return bool(
            other.author == self.author
            and other.horizon == self.horizon
            and other.patch == self.patch
        )


@dataclass
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
    name = Column(String(255))
    type = Column(String(50))
    version = Column(String(255))
    author = Column(String(255))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    path = Column(String())
    folder = Column(String, nullable=True)
    parent_id = Column(
        String(36), ForeignKey("study.id", name="fk_study_study_id")
    )
    public_mode = Column(Enum(PublicMode), default=PublicMode.NONE)
    owner_id = Column(Integer, ForeignKey(Identity.id), nullable=True)
    archived = Column(Boolean(), default=False)
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=lambda: groups_metadata, cascade="")
    additional_data = relationship(
        StudyAdditionalData,
        uselist=False,
        cascade="all, delete, delete-orphan",
    )
    __mapper_args__ = {"polymorphic_identity": "study", "polymorphic_on": type}

    def __str__(self) -> str:
        return f"[Study] id={self.id}, type={self.type}, name={self.name}, version={self.version}, updated_at={self.updated_at}, owner={self.owner}, groups={[str(u) + ',' for u in self.groups]}"

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


@dataclass
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
    workspace = Column(String(255), default=DEFAULT_WORKSPACE_NAME)
    missing = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "rawstudy",
    }

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


@dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: List[Group]


class PatchStudy(BaseModel):
    scenario: Optional[str] = None
    doc: Optional[str] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    tags: List[str] = []


class PatchArea(BaseModel):
    country: Optional[str] = None
    tags: List[str] = []


class PatchCluster(BaseModel):
    type: Optional[str] = None
    code_oi: Optional[str] = None

    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            return "-".join(word for word in string.split("_"))


class PatchOutputs(BaseModel):
    reference: Optional[str] = None


class Patch(BaseModel):
    study: Optional[PatchStudy] = None
    areas: Optional[Dict[str, PatchArea]] = None
    thermal_clusters: Optional[Dict[str, PatchCluster]] = None
    outputs: Optional[PatchOutputs] = None


class OwnerInfo(BaseModel):
    id: Optional[int] = None
    name: str


class StudyMetadataDTO(BaseModel):
    id: str
    name: str
    version: int
    created: str
    updated: str
    type: str
    owner: OwnerInfo
    groups: List[GroupDTO]
    public_mode: PublicMode
    workspace: str
    managed: bool
    archived: bool
    horizon: Optional[str]
    scenario: Optional[str]
    status: Optional[str]
    doc: Optional[str]
    folder: Optional[str] = None
    tags: List[str] = []


class StudyMetadataPatchDTO(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None
    horizon: Optional[str] = None
    scenario: Optional[str] = None
    status: Optional[str] = None
    doc: Optional[str] = None
    tags: List[str] = []


class StudySimSettingsDTO(BaseModel):
    general: Dict[str, Any]
    input: Dict[str, Any]
    output: Dict[str, Any]
    optimization: Dict[str, Any]
    otherPreferences: Dict[str, Any]
    advancedParameters: Dict[str, Any]
    seedsMersenneTwister: Dict[str, Any]
    playlist: Optional[List[int]] = None


class StudySimResultDTO(BaseModel):
    name: str
    type: str
    settings: StudySimSettingsDTO
    completionDate: str
    referenceStatus: bool
    synchronized: bool
    status: str


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
    years: Optional[List[int]]
    level: StudyDownloadLevelDTO
    filterIn: Optional[str]
    filterOut: Optional[str]
    filter: Optional[List[str]]
    columns: Optional[List[str]]
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
    data: List[Optional[float]] = list()


class TimeSeriesData(BaseModel):
    type: StudyDownloadType
    name: str
    data: Dict[str, List[TimeSerie]] = dict()


class MatrixAggregationResultDTO(BaseModel):
    index: MatrixIndex
    data: List[TimeSeriesData]
    warnings: List[str]


class MatrixAggregationResult(BaseModel):
    index: MatrixIndex
    data: Dict[Tuple[StudyDownloadType, str], Dict[str, List[TimeSerie]]]
    warnings: List[str]

    def to_dto(self) -> MatrixAggregationResultDTO:
        return MatrixAggregationResultDTO(
            index=self.index,
            data=[
                TimeSeriesData(
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
