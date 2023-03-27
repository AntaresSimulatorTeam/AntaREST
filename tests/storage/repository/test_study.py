from datetime import datetime
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker  # type: ignore

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.interfaces.cache import CacheConstants
from antarest.core.persistence import Base
from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.login.model import User, Group
from antarest.study.common.utils import get_study_information
from antarest.study.model import (
    Study,
    RawStudy,
    DEFAULT_WORKSPACE_NAME,
    StudyContentStatus,
    PublicMode,
)
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.conftest import with_db_context


def test_cyclelife():
    engine = create_engine("sqlite:///:memory:", echo=False)

    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")
    Base.metadata.create_all(engine)
    DBSessionMiddleware(
        Mock(),
        custom_engine=engine,
        session_args={"autocommit": False, "autoflush": False},
    )

    with db():
        repo = StudyMetadataRepository(LocalCache())
        a = Study(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )
        b = RawStudy(
            name="b",
            version="43",
            author="Morpheus",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )
        c = RawStudy(
            name="c",
            version="43",
            author="Trinity",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            missing=datetime.utcnow(),
        )
        d = VariantStudy(
            name="d",
            version="43",
            author="Mr. Anderson",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
        )

        a = repo.save(a)
        b = repo.save(b)
        repo.save(c)
        repo.save(d)
        assert b.id
        c = repo.get(a.id)
        assert a == c

        assert len(repo.get_all()) == 3
        assert len(repo.get_all_raw(show_missing=True)) == 2
        assert len(repo.get_all_raw(show_missing=False)) == 1

        repo.delete(a.id)
        assert repo.get(a.id) is None


def test_study_inheritance():
    engine = create_engine("sqlite:///:memory:", echo=False)
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
        repo = StudyMetadataRepository(LocalCache())
        a = RawStudy(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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


@with_db_context
def test_cache():
    user = User(id=0, name="admin")
    group = Group(id="my-group", name="group")

    cache = LocalCache()

    with db():
        repo = StudyMetadataRepository(cache)
        a = RawStudy(
            name="a",
            version="42",
            author="John Smith",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            public_mode=PublicMode.FULL,
            owner=user,
            groups=[group],
            workspace=DEFAULT_WORKSPACE_NAME,
            path="study",
            content_status=StudyContentStatus.WARNING,
        )

        repo.save(a)
        cache.put(
            CacheConstants.STUDY_LISTING.value,
            {a.id: get_study_information(a)},
        )
        repo.save(a)
        repo.delete(a.id)

        assert len(cache.get(CacheConstants.STUDY_LISTING.value)) == 0
