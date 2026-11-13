# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from pathlib import Path

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.output.filestudy.gems_views import extract_gems_views
from antarest.output.model.gems_views import GemsTaxonomyViews
from antarest.output.storage.file.repository import DbOutputGemsViews, FileOutputRepository
from antarest.study.model import Study
from tests.helpers import create_study


@pytest.fixture
def gems_views(project_path: Path) -> list[GemsTaxonomyViews]:
    return extract_gems_views(project_path / "tests/output/filestudy/data/20261104-1636eco-gems_views")


@pytest.fixture
def study_id() -> str:
    with db():
        db.session.add(create_study(id="my-study"))
        db.session.commit()
    return "my-study"


def test_gems_views_round_trip(study_id: str, gems_views: list[GemsTaxonomyViews]) -> None:
    repository = FileOutputRepository()
    with db():
        assert repository.get_output_gems_views(study_id, "output") is None

        repository.save_output_gems_views(study_id, "output", gems_views)
        assert repository.get_output_gems_views(study_id, "output") == gems_views

        assert repository.get_output_gems_views(study_id, "other-output") is None

        with pytest.raises(IntegrityError):
            repository.save_output_gems_views(study_id, "output", [])
        db.session.rollback()
        assert repository.get_output_gems_views(study_id, "output") == gems_views


def test_delete_output_gems_views(study_id: str, gems_views: list[GemsTaxonomyViews]) -> None:
    repository = FileOutputRepository()
    with db():
        repository.save_output_gems_views(study_id, "output", gems_views)
        repository.save_output_gems_views(study_id, "other-output", gems_views)

        repository.delete_output_gems_views(study_id, "output")
        assert repository.get_output_gems_views(study_id, "output") is None
        assert repository.get_output_gems_views(study_id, "other-output") == gems_views

        repository.delete_output_gems_views(study_id, "output")


def test_gems_views_are_deleted_with_the_study(study_id: str, gems_views: list[GemsTaxonomyViews]) -> None:
    repository = FileOutputRepository()
    with db():
        repository.save_output_gems_views(study_id, "output", gems_views)

        db.session.execute(delete(Study).where(Study.id == study_id))
        db.session.commit()
        assert db.session.execute(select(DbOutputGemsViews)).all() == []
