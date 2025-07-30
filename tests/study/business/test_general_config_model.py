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
from typing import Any, List

import pytest
from antares.study.version import StudyVersion

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.config.general_model import (
    GeneralConfig,
    initialize_default_values,
    validate_general_config_version,
)
from antarest.study.model import STUDY_VERSION_7_0, STUDY_VERSION_7_1, STUDY_VERSION_7_2


def test_general_config_default_values():
    config = GeneralConfig()
    initialize_default_values(config, version=STUDY_VERSION_7_2)
    assert config.filtering is None
    assert config.geographic_trimming is False
    assert config.thematic_trimming is False


@pytest.mark.parametrize(
    "invalid_versions,valid_versions,fields",
    [
        ([STUDY_VERSION_7_1], [STUDY_VERSION_7_0], {"filtering": True}),
        ([STUDY_VERSION_7_0], [STUDY_VERSION_7_1], {"thematic_trimming": True}),
        ([STUDY_VERSION_7_0], [STUDY_VERSION_7_1], {"geographic_trimming": True}),
    ],
)
def test_config_version_validation(
    invalid_versions: List[StudyVersion], valid_versions: List[StudyVersion], fields: dict[str, Any]
):
    """
    Check that the presence of the fields raise an error for "invalid_versions", but not for "valid_versions"
    """
    config = GeneralConfig.model_validate(fields)
    for version in invalid_versions:
        with pytest.raises(InvalidFieldForVersionError, match="is not a valid field for study version"):
            validate_general_config_version(config, version)
    for version in valid_versions:
        validate_general_config_version(config, version)
