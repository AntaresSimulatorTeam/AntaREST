import uuid
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import relationship

from antarest.core.persistence import Base
from sqlalchemy import Column, String, ForeignKey, DateTime

from antarest.study.model import (
    Study,
    StudyContentStatus,
    DEFAULT_WORKSPACE_NAME,
)


@dataclass
class VariantStudySnapshot(Base):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "variant_study_snapshot"

    id = Column(
        String(36),
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    created_at = Column(DateTime)
    path = Column(String(255))
    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }


@dataclass
class VariantStudy(Study):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "variantstudy"

    id = Column(
        String(36),
        ForeignKey("study.id"),
        primary_key=True,
    )
    path = Column(String(255))
    __mapper_args__ = {
        "polymorphic_identity": "variantstudy",
    }
    variant_study_snapshot = relationship("VariantStudySnapshot")
    variant_snapshot_id = Column(
        String(36), ForeignKey(VariantStudySnapshot.id), nullable=True
    )
