import typing as t
from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session  # type: ignore

from antarest.core.interfaces.cache import ICache
from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyFilter, StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from tests.db_statement_recorder import DBStatementRecorder


@pytest.mark.parametrize(
    "managed, studies_ids, exists, expected_ids",
    [
        (None, [], False, {"5", "6"}),
        (None, [], True, {"1", "2", "3", "4", "7", "8"}),
        (None, [], None, {"1", "2", "3", "4", "5", "6", "7", "8"}),
        (None, [1, 3, 5, 7], False, {"5"}),
        (None, [1, 3, 5, 7], True, {"1", "3", "7"}),
        (None, [1, 3, 5, 7], None, {"1", "3", "5", "7"}),
        (True, [], False, {"5"}),
        (True, [], True, {"1", "2", "3", "4", "8"}),
        (True, [], None, {"1", "2", "3", "4", "5", "8"}),
        (True, [1, 3, 5, 7], False, {"5"}),
        (True, [1, 3, 5, 7], True, {"1", "3"}),
        (True, [1, 3, 5, 7], None, {"1", "3", "5"}),
        (True, [2, 4, 6, 8], True, {"2", "4", "8"}),
        (True, [2, 4, 6, 8], None, {"2", "4", "8"}),
        (False, [], False, {"6"}),
        (False, [], True, {"7"}),
        (False, [], None, {"6", "7"}),
        (False, [1, 3, 5, 7], False, set()),
        (False, [1, 3, 5, 7], True, {"7"}),
        (False, [1, 3, 5, 7], None, {"7"}),
    ],
)
def test_repository_get_all(
    db_session: Session,
    managed: t.Union[bool, None],
    studies_ids: t.Union[t.List[str], None],
    exists: t.Union[bool, None],
    expected_ids: set,
):
    test_workspace = "test-repository"
    icache: Mock = Mock(spec=ICache)
    repository = StudyMetadataRepository(cache_service=icache, session=db_session)

    study_1 = VariantStudy(id=1)
    study_2 = VariantStudy(id=2)
    study_3 = VariantStudy(id=3)
    study_4 = VariantStudy(id=4)
    study_5 = RawStudy(id=5, missing=datetime.now(), workspace=DEFAULT_WORKSPACE_NAME)
    study_6 = RawStudy(id=6, missing=datetime.now(), workspace=test_workspace)
    study_7 = RawStudy(id=7, missing=None, workspace=test_workspace)
    study_8 = RawStudy(id=8, missing=None, workspace=DEFAULT_WORKSPACE_NAME)

    db_session.add_all([study_1, study_2, study_3, study_4, study_5, study_6, study_7, study_8])
    db_session.commit()

    # use the db recorder to check that:
    # 1- retrieving all studies requires only 1 query
    # 2- accessing studies attributes does require additional queries to db
    # 3- having an exact total of queries equals to 1
    with DBStatementRecorder(db_session.bind) as db_recorder:
        all_studies = repository.get_all(
            study_filter=StudyFilter(managed=managed, studies_ids=studies_ids, exists=exists)
        )
        _ = [s.owner for s in all_studies]
        _ = [s.groups for s in all_studies]
        _ = [s.additional_data for s in all_studies]
    assert len(db_recorder.sql_statements) == 1, str(db_recorder)

    if expected_ids is not None:
        assert set([s.id for s in all_studies]) == expected_ids
