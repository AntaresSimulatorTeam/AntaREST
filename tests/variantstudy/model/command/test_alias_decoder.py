# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from unittest.mock import Mock, patch

import pytest

from antarest.study.storage.variantstudy.business.utils import AliasDecoder


@pytest.mark.unit_test
@pytest.mark.parametrize("alias,expected_call", [("@links_series/a/b", "links_series")])
def test_alias_decoder_decode(alias: str, expected_call: str):
    with patch.object(AliasDecoder, expected_call) as mocked_method:
        AliasDecoder.decode(alias, study=Mock())
        mocked_method.assert_called_once()


@pytest.mark.unit_test
def test_alias_decoder_decode_raises_error():
    with pytest.raises(NotImplementedError):
        AliasDecoder.decode("@non_existent_alias", study=Mock())


@pytest.mark.unit_test
def test_alias_decoder_links_series():
    area_from = "a"
    area_to = "b"
    alias = f"@links_series/{area_from}/{area_to}"
    file_study_mock = Mock()

    file_study_mock.config.version = 800
    assert AliasDecoder.links_series(alias, file_study_mock) == f"input/links/{area_from}/{area_to}"

    file_study_mock.config.version = 830
    assert AliasDecoder.links_series(alias, file_study_mock) == f"input/links/{area_from}/{area_to}_parameters"
