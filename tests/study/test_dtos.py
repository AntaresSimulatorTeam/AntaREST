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


from antares.study.version import StudyVersion

from antarest.study.dtos import StudyDataSynthesis


class TestStudyDataSynthesis:
    """
    Test the `StudyDataSynthesis` DTO.
    """

    def test_bindings_groups_is_a_set(self) -> None:
        """
        Ensure that `bindings_groups` behaves like a set: adding the same group
        twice should result in a single entry.
        """
        synthesis = StudyDataSynthesis(
            study_id="study-id",
            version=StudyVersion.parse("8.7"),
            bindings_groups={"group_A", "group_A", "group_B"},
        )

        assert isinstance(synthesis.bindings_groups, set)
        assert synthesis.bindings_groups == {"group_A", "group_B"}

    def test_bindings_groups_deduplicates_from_list(self) -> None:
        """
        Pydantic must coerce a list containing duplicates into a set,
        deduplicating values automatically.
        """
        synthesis = StudyDataSynthesis(
            study_id="study-id",
            version=StudyVersion.parse("8.7"),
            bindings_groups=["group_A", "group_A", "group_B", "group_B"],
        )

        assert isinstance(synthesis.bindings_groups, set)
        assert synthesis.bindings_groups == {"group_A", "group_B"}
