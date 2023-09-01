import json
import uuid
from dataclasses import dataclass

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.model import CommandDTO


@dataclass
class VariantStudySnapshot(Base):  # type: ignore
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
    last_executed_command = Column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }

    def __str__(self) -> str:
        return f"[Snapshot]: id={self.id}, created_at={self.created_at}"


@dataclass
class CommandBlock(Base):  # type: ignore
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
    version = Column(Integer)
    args = Column(String())

    def to_dto(self) -> CommandDTO:
        return CommandDTO(id=self.id, action=self.command, args=json.loads(self.args))


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
    generation_task = Column(String(), nullable=True)

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

    def __str__(self) -> str:
        return super().__str__() + f", snapshot={self.snapshot}"
