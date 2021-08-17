import uuid
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import relationship

from antarest.core.persistence import Base
from sqlalchemy import Column, String, ForeignKey, DateTime, Table, Integer

from antarest.study.model import (
    Study,
)


command_metadata = Table(
    "command_metadata",
    Base.metadata,
    Column("commandblock_id", String(36), ForeignKey("commandblock.id")),
    Column("variantstudy_id", String(36), ForeignKey("variantstudy.id")),
)


@dataclass
class VariantStudySnapshot(Base):
    """
    Variant Study Snapshot based entity implementation.
    """

    __tablename__ = "variant_study_snapshot"

    id = Column(
        String(36),
        ForeignKey("variantstudy.id"),
        primary_key=True,
    )
    created_at = Column(DateTime)
    path = Column(String(255))
    variant_study = relationship("VariantStudy")
    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }


@dataclass
class CommandBlock(Base):
    """
    Command Block based entity implementation.
    """

    __tablename__ = "commandblock"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    study_id = Column(String(36), ForeignKey("variantstudy.id"))
    index = Column(Integer)
    command = Column(String(255))
    args = Column(String(255))
    variant_study = relationship("VariantStudy")
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
    variant_study_snapshot = relationship(
        "VariantStudySnapshot", uselist=False
    )
    variant_snapshot_id = Column(
        String(36), ForeignKey("variant_study_snapshot.id")
    )
    command_block = relationship(
        CommandBlock,
        order_by="CommandBlock.index",
        secondary=lambda: command_metadata,
        cascade="",
    )
