# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import datetime
from unittest.mock import Mock

from sqlalchemy.orm import Session

from antarest.core.interfaces.cache import ICache
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from tests.helpers import create_raw_study, create_variant_study


class TestVariantStudyRepository:
    def test_get_children(self, db_session: Session) -> None:
        """
        Given a root study with children and a grandchild
        When getting the children of the root study
        Then the children are returned in reverse chronological order
        """
        repository = VariantStudyRepository(cache_service=Mock(spec=ICache), session=db_session)

        # Create a root study
        raw_study = create_raw_study(name="My Root")
        db_session.add(raw_study)
        db_session.commit()

        # Ensure the root study has no children
        children = repository.get_children(parent_id=raw_study.id)
        assert children == []

        # Prepare some dates for the children
        day1 = datetime.datetime(2023, 1, 1)
        day2 = datetime.datetime(2023, 1, 2)
        day3 = datetime.datetime(2023, 1, 3)
        day4 = datetime.datetime(2023, 1, 4)

        # Create two variant studies of the same parent
        variant1 = create_variant_study(name="My Variant 1", parent_id=raw_study.id, created_at=day1)
        variant2 = create_variant_study(name="My Variant 2", parent_id=raw_study.id, created_at=day3)
        db_session.add_all([variant1, variant2])
        db_session.commit()

        # Ensure the root study has 2 children
        children = repository.get_children(parent_id=raw_study.id)
        assert children == [variant2, variant1]
        assert children[0].created_at > children[1].created_at

        # Ensure variants have no children
        children = repository.get_children(parent_id=variant1.id)
        assert children == []
        children = repository.get_children(parent_id=variant2.id)
        assert children == []

        # Add a variant study between the two existing ones (in reverse chronological order)
        variant3 = create_variant_study(name="My Variant 3", parent_id=raw_study.id, created_at=day2)
        db_session.add(variant3)
        db_session.commit()

        # Ensure the root study has 3 children in chronological order
        children = repository.get_children(parent_id=raw_study.id)
        assert children == [variant2, variant3, variant1]
        assert children[0].created_at > children[1].created_at > children[2].created_at

        # Add a variant of a variant
        variant3a = create_variant_study(name="My Variant 3a", parent_id=variant3.id, created_at=day4)
        db_session.add(variant3a)
        db_session.commit()

        # Ensure the root study has the 3 same children
        children = repository.get_children(parent_id=raw_study.id)
        assert children == [variant2, variant3, variant1]
