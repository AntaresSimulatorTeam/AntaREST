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
from antares.study.version import StudyVersion

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.config.compatibility_parameters_model import (
    CompatibilityParametersUpdate,
    HydroPmax,
    validate_compatibility_parameters_against_version,
)


class TestValidateCompatibilityParametersAgainstVersion:
    def test_hydro_pmax_rejected_before_920(self) -> None:
        with pytest.raises(InvalidFieldForVersionError):
            validate_compatibility_parameters_against_version(
                StudyVersion.parse("8.8"),
                CompatibilityParametersUpdate(hydro_pmax=HydroPmax.HOURLY),
            )

    def test_hydro_pmax_accepted_from_920(self) -> None:
        validate_compatibility_parameters_against_version(
            StudyVersion.parse("9.2"),
            CompatibilityParametersUpdate(hydro_pmax=HydroPmax.HOURLY),
        )

    def test_reserves_enabled_rejected_before_1000(self) -> None:
        with pytest.raises(InvalidFieldForVersionError):
            validate_compatibility_parameters_against_version(
                StudyVersion.parse("9.2"),
                CompatibilityParametersUpdate(reserves_enabled=True),
            )

    def test_reserves_enabled_accepted_from_1000(self) -> None:
        validate_compatibility_parameters_against_version(
            StudyVersion.parse("10.0"),
            CompatibilityParametersUpdate(reserves_enabled=True),
        )

    def test_no_fields_set_always_passes(self) -> None:
        validate_compatibility_parameters_against_version(
            StudyVersion.parse("8.0"),
            CompatibilityParametersUpdate(),
        )
