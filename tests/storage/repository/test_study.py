from datetime import datetime
from unittest.mock import Mock

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker  # type: ignore

from antarest.core.config import Config
from antarest.core.persistence import Base
from antarest.login.model import User, RoleType, Group
from antarest.login.repository import UserRepository
from antarest.storage.model import (
    Study,
    RawStudy,
    DEFAULT_WORKSPACE_NAME,
    StudyContentStatus,
    PublicMode,
)
from antarest.storage.repository.study_metadata import StudyMetadataRepository


def test_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = StudyMetadataRepository()
        a = Study(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )
        b = Study(
            name="b",
            version="43",
            author="Morpheus",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )

        a = repo.save(a)
        b = repo.save(b)
        assert b.id
        c = repo.get(a.id)
        assert a == c

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_study_inheritance():
    engine = create_engine("sqlite:///:memory:", echo=True)
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = StudyMetadataRepository()
        a = RawStudy(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace=DEFAULT_WORKSPACE_NAME,
            path="study",
            content_status=StudyContentStatus.WARNING,
        )

        repo.save(a)
        b = repo.get(a.id)

        assert isinstance(b, RawStudy)
        assert b.path == "study"
