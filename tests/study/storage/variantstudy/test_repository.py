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
import uuid

import pytest
from sqlalchemy.orm import Session

from antarest.study.model import DEFAULT_WORKSPACE_NAME, RawStudy
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.variantstudy.model.dbmodel import (
    CommandsListVersion,
    LineageVersions,
    StudyDataVersion,
    VariantStudy,
    VariantStudySnapshot,
)
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
    variant_repo = VariantStudyRepository(db_session)

    # Build a tree of root > variant1 (data version 1) > variant2 (data version 0)
    root_study = RawStudy(name="root study", workspace=DEFAULT_WORKSPACE_NAME, version="8.6", path="/my-dir")
    db_session.add(root_study)
    db_session.flush()

    variant1 = VariantStudy(name="variant 1", version="8.6", path="/tutu", parent_id=root_study.id)
    variant1.commands_version = CommandsListVersion(version=1)
    db_session.add(variant1)
    db_session.flush()

    variant2 = VariantStudy(name="variant 2", version="8.6", path="/tutu", parent_id=variant1.id)
    variant2.commands_version = CommandsListVersion(version=0)

    db_session.add(variant2)
    db_session.commit()

    # Checks we find the correct lineage data versions
    assert variant_repo.get_lineage_versions(variant2.id) == LineageVersions(
        [StudyDataVersion(variant1.id, 1), StudyDataVersion(variant2.id, 0)]
    )


def test_snapshot_is_up_to_date(db_session: Session):
    variant_repo = VariantStudyRepository(db_session)

    # Build a tree of root > variant1 (data version 1) > variant2 (data version 0)
    root_study = RawStudy(
        id=str(uuid.uuid4()), name="root study", workspace=DEFAULT_WORKSPACE_NAME, version="8.6", path="/my-dir"
    )

    variant1 = VariantStudy(
        id=str(uuid.uuid4()), name="variant 1", version="8.6", path="/tutu", parent_id=root_study.id
    )
    variant1.commands_version = CommandsListVersion(version=1)

    variant2 = VariantStudy(id=str(uuid.uuid4()), name="variant 2", version="8.6", path="/tutu", parent_id=variant1.id)
    variant2.commands_version = CommandsListVersion(version=2)

    variant2.snapshot = VariantStudySnapshot(
        last_executed_command=None,
        lineage_versions=LineageVersions.from_tuples([(variant1.id, 1), (variant2.id, 2)]),
    )

    db_session.add_all((root_study, variant1, variant2))
    db_session.commit()

    # Snapshot lineage has been created up to date
    assert variant_repo.is_snapshot_up_to_date(variant2.id)

    # If snapshot does not exist, we consider it is not up to date
    variant2.snapshot = None
    db_session.commit()
    assert not variant_repo.is_snapshot_up_to_date(variant2.id)

    # If the variant itself has another version, we consider it is not up to date
    variant2.snapshot = VariantStudySnapshot(
        last_executed_command=None,
        lineage_versions=LineageVersions.from_tuples([(variant1.id, 1), (variant2.id, 1)]),
    )
    db_session.commit()
    assert not variant_repo.is_snapshot_up_to_date(variant2.id)

    # If a parent has an older version, we consider it is not up to date
    variant2.snapshot = VariantStudySnapshot(
        last_executed_command=None,
        lineage_versions=LineageVersions.from_tuples([(variant1.id, 0), (variant2.id, 2)]),
    )
    db_session.commit()
    assert not variant_repo.is_snapshot_up_to_date(variant2.id)

    # If lineage has changed, we consider it is not up to date
    variant2.snapshot = VariantStudySnapshot(
        last_executed_command=None,
        lineage_versions=LineageVersions.from_tuples([(variant2.id, 0)]),
    )
    db_session.commit()
    assert not variant_repo.is_snapshot_up_to_date(variant2.id)
