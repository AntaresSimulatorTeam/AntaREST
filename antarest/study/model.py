import enum
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from dataclasses_json import DataClassJsonMixin  # type: ignore
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, DateTime, Table, ForeignKey, Enum, Boolean  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.login.model import Group, Identity, GroupDTO

DEFAULT_WORKSPACE_NAME = "default"

groups_metadata = Table(
    "group_metadata",
    Base.metadata,
    Column("group_id", String(36), ForeignKey("groups.id")),
    Column("study_id", String(36), ForeignKey("study.id")),
)


class StudyContentStatus(enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PublicMode(enum.Enum):
    NONE = "NONE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    EDIT = "EDIT"
    FULL = "FULL"


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
    parent_id = Column(
        String(36), ForeignKey("study.id", name="fk_study_study_id")
    )
    public_mode = Column(Enum(PublicMode), default=PublicMode.NONE)
    owner_id = Column(Integer, ForeignKey(Identity.id), nullable=True)
    archived = Column(Boolean(), default=False)
    owner = relationship(Identity, uselist=False)
    groups = relationship(Group, secondary=lambda: groups_metadata, cascade="")
    __mapper_args__ = {"polymorphic_identity": "study", "polymorphic_on": type}

    def __str__(self) -> str:
        return f"Metadata(id={self.id}, name={self.name}, version={self.version}, owner={self.owner}, groups={[str(u)+',' for u in self.groups]}"

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
    path = Column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "rawstudy",
    }


@dataclass
class StudyFolder:
    """
    DTO used by watcher to keep synchronized studies and workspace organization and database
    """

    path: Path
    workspace: str
    groups: List[Group]


class PatchLeaf:
    def patch(self, new_patch: "PatchLeaf") -> "PatchLeaf":
        new_patch_leaf = deepcopy(self)
        for attribute_name in self.__dict__.keys():
            new_attribute = getattr(new_patch, attribute_name, None)
            old_attribute = getattr(self, attribute_name, None)
            setattr(
                new_patch_leaf,
                attribute_name,
                new_attribute if new_attribute is not None else old_attribute,
            )
        return new_patch_leaf

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PatchLeaf):
            return NotImplemented

        eq: bool = True
        for attribute in self.__dict__.keys():
            eq = eq and (
                getattr(self, attribute, None)
                == getattr(other, attribute, None)
            )
            if not eq:
                return eq
        return eq


class PatchLeafDict(Dict[str, PatchLeaf]):
    def patch(self, new_patch_leaf_dict: "PatchLeafDict") -> "PatchLeafDict":
        merged_dict = deepcopy(self)
        for new_dict_key, new_dict_value in new_patch_leaf_dict.items():
            if new_dict_key not in self.keys():
                merged_dict[new_dict_key] = new_dict_value
            else:
                merged_dict[new_dict_key] = self[new_dict_key].patch(
                    new_dict_value
                )

        return merged_dict


T = TypeVar("T")  # to fix mypy


class PatchNode:
    def patch(self: T, new_patch: T) -> T:
        merged_patch = deepcopy(self)
        for leaf_name in self.__dict__.keys():
            old_leaf = getattr(self, leaf_name, None)
            new_leaf = getattr(new_patch, leaf_name, None)
            if old_leaf is None:
                setattr(
                    merged_patch,
                    leaf_name,
                    new_leaf,
                )
            elif new_leaf is not None:
                setattr(
                    merged_patch,
                    leaf_name,
                    old_leaf.patch(new_leaf),
                )
        return merged_patch


class PatchStudy(BaseModel, PatchLeaf):
    scenario: Optional[str] = None
    doc: Optional[str] = None
    status: Optional[str] = None


class PatchArea(BaseModel, PatchLeaf):
    country: Optional[str] = None


class PatchOutputs(BaseModel):
    reference: Optional[str] = None


class Patch(BaseModel, PatchNode):
    study: Optional[PatchStudy] = None
    areas: Optional[PatchLeafDict] = None
    outputs: Optional[PatchOutputs] = None


class OwnerInfo(BaseModel):
    id: Optional[int] = None
    name: str


class StudyMetadataDTO(BaseModel):
    id: str
    name: str
    version: int
    created: int
    updated: int
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


class StudyMetadataPatchDTO(BaseModel):
    name: Optional[str] = None
    horizon: Optional[str] = None
    scenario: Optional[str] = None
    status: Optional[str] = None
    doc: Optional[str] = None


class StudySimSettingsDTO(BaseModel):
    general: Dict[str, Any]
    input: Dict[str, Any]
    output: Dict[str, Any]
    optimization: Dict[str, Any]
    otherPreferences: Dict[str, Any]
    advancedParameters: Dict[str, Any]
    seedsMersenneTwister: Dict[str, Any]


class StudySimResultDTO(BaseModel):
    name: str
    type: str
    settings: StudySimSettingsDTO
    completionDate: str
    referenceStatus: bool
    synchronized: bool
    status: str


class StudyDownloadType(enum.Enum):
    LINK = "LINK"
    CLUSTER = "CLUSTER"
    AREA = "AREA"

    @staticmethod
    def from_dict(value: str) -> "StudyDownloadType":
        mapping = {
            "LINK": StudyDownloadType.LINK,
            "CLUSTER": StudyDownloadType.CLUSTER,
            "AREA": StudyDownloadType.AREA,
        }

        if value in mapping:
            return mapping[value]
        else:
            raise ValueError(f"any StudyDownloadType for value {value}")

    def to_dict(self) -> str:
        return str(self.value)


class StudyDownloadLevelDTO(enum.Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    HOURLY = "hourly"

    @staticmethod
    def from_dict(value: str) -> "StudyDownloadLevelDTO":
        mapping = {
            "annual": StudyDownloadLevelDTO.ANNUAL,
            "monthly": StudyDownloadLevelDTO.MONTHLY,
            "weekly": StudyDownloadLevelDTO.WEEKLY,
            "daily": StudyDownloadLevelDTO.DAILY,
            "hourly": StudyDownloadLevelDTO.HOURLY,
        }

        if value in mapping:
            return mapping[value]
        else:
            raise ValueError(f"any StudyDownloadLevelDTO for value {value}")

    def to_dict(self) -> str:
        return str(self.value)


class StudyDownloadDTO(BaseModel):
    """
    DTO used to download outputs
    """

    type: str
    years: Optional[List[int]]
    level: str
    filterIn: Optional[str]
    filterOut: Optional[str]
    filter: Optional[List[str]]
    columns: Optional[List[str]]
    synthesis: bool = False
    includeClusters: bool = False


class MatrixIndex(BaseModel):
    startDate: str = ""
    step: int = 3600000


class MatrixAggregationResult(BaseModel):
    index: MatrixIndex
    data: Dict[str, Dict[str, Dict[str, List[Optional[float]]]]]
    warnings: List[str]
