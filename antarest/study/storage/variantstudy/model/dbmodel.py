import datetime
import json
import typing as t
import uuid
from pathlib import Path

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String  # type: ignore
from sqlalchemy.orm import relationship  # type: ignore

from antarest.core.persistence import Base
from antarest.study.model import Study
from antarest.study.storage.variantstudy.model.model import CommandDTO


class VariantStudySnapshot(Base):  # type: ignore
    """
    Variant Study Snapshot based entity implementation.
    """

    __tablename__ = "variant_study_snapshot"

    id: str = Column(
        String(36),
        ForeignKey("variantstudy.id"),
        primary_key=True,
    )
    created_at: datetime.date = Column(DateTime)
    last_executed_command: t.Optional[str] = Column(String(), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "variant_study_snapshot",
    }

    def __str__(self) -> str:
        return f"[Snapshot] id={self.id}, created_at={self.created_at}"


class CommandBlock(Base):  # type: ignore
    """
    Command Block based entity implementation.
    """

    __tablename__ = "commandblock"

    id: str = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
    )
    study_id: str = Column(String(36), ForeignKey("variantstudy.id"))
    index: int = Column(Integer)
    command: str = Column(String(255))
    version: int = Column(Integer)
    args: str = Column(String())

    def to_dto(self) -> CommandDTO:
        return CommandDTO(id=self.id, action=self.command, args=json.loads(self.args))

    def __str__(self) -> str:
        return (
            f"CommandBlock(id={self.id!r},"
            f" study_id={self.study_id!r},"
            f" index={self.index!r},"
            f" command={self.command!r},"
            f" version={self.version!r},"
            f" args={self.args!r})"
        )


class VariantStudy(Study):
    """
    Study filesystem based entity implementation.
    """

    __tablename__ = "variantstudy"

    id: str = Column(
        String(36),
        ForeignKey("study.id"),
        primary_key=True,
    )
    generation_task: t.Optional[str] = Column(String(), nullable=True)

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

    @property
    def snapshot_dir(self) -> Path:
        """Get the path of the snapshot directory."""
        return Path(self.path) / "snapshot"

    def is_snapshot_up_to_date(self) -> bool:
        """Check if the snapshot exists and is up-to-date."""
        return (
            (self.snapshot is not None)
            and (self.snapshot.created_at >= self.updated_at)
            and (self.snapshot_dir / "study.antares").is_file()
        )
