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
import pytest
from sqlalchemy.orm import Session

from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.repository import VariantStudyRepository


def test_get_study_lineage(db_session: Session):
    study_repo = StudyMetadataRepository(db_session)
    variant_repo = VariantStudyRepository(db_session)

    root_study = study_repo.save(
        RawStudy(name="root study", workspace=DEFAULT_WORKSPACE_NAME, version="8.6", path="/my-dir")
    )

    variant1 = variant_repo.save(VariantStudy(name="variant 1", version="8.6", path="/tutu", parent_id=root_study.id))
    variant2 = variant_repo.save(VariantStudy(name="variant 2", version="8.6", path="/tutu", parent_id=variant1.id))
    tree_root, tree_studies = variant_repo.get_study_lineage(variant2.id)

    assert tree_root.id == root_study.id
    assert tuple(s.id for s in tree_studies) == (variant1.id, variant2.id)

    from antarest.core.exceptions import StudyNotFoundError

    with pytest.raises(StudyNotFoundError):
        variant_repo.get_study_lineage("non-existent-variant-id")


def test_get_lineage_versions(db_session: Session):
    pass
