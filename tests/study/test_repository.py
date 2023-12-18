import typing as t
from datetime import datetime
from unittest.mock import Mock

import pytest

from antarest.core.interfaces.cache import ICache
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.helpers import with_db_context


@with_db_context
@pytest.mark.parametrize(
    "managed, studies_ids, exists, expected_ids",
    [
        (None, None, False, {"1", "2", "3", "4", "5", "6", "7", "8"}),
        (None, None, True, {"1", "2", "3", "4", "7", "8"}),
        (None, [1, 3, 5, 7], False, {"1", "3", "5", "7"}),
        (None, [1, 3, 5, 7], True, {"1", "3", "7"}),
        (True, None, False, {"1", "2", "3", "4", "5", "8"}),
        (True, None, True, {"1", "2", "3", "4", "8"}),
        (True, [1, 3, 5, 7], False, {"1", "3", "5"}),
        (True, [1, 3, 5, 7], True, {"1", "3"}),
        (True, [2, 4, 6, 8], True, {"2", "4", "8"}),
        (False, None, False, {"6", "7"}),
        (False, None, True, {"7"}),
        (False, [1, 3, 5, 7], False, {"7"}),
        (False, [1, 3, 5, 7], True, {"7"}),
    ],
)
def test_repository_get_all(
    managed: t.Union[bool, None],
    studies_ids: t.Union[t.List[str], None],
    exists: bool,
    expected_ids: set,
):
    test_workspace = "test-repository"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = VariantStudy(id=3)
    study_4 = VariantStudy(id=4)
    study_5 = RawStudy(id=5, missing=datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, missing=datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id=7, missing=None, workspace=test_workspace)
    study_8 = RawStudy(id=8, missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session = repository.session
    db_session.add(study_1)
    db_session.add(study_2)
    db_session.add(study_3)
    db_session.add(study_4)
    db_session.add(study_5)
    db_session.add(study_6)
    db_session.add(study_7)
    db_session.add(study_8)
    db_session.commit()

    all_studies = repository.get_all(managed=managed, studies_ids=studies_ids, exists=exists)

    if expected_ids is not None:
        assert set([s.id for s in all_studies]) == expected_ids
