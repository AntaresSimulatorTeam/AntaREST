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

from unittest.mock import Mock, patch

import pytest

from antarest.study.model import STUDY_VERSION_8, STUDY_VERSION_8_3
from antarest.study.storage.variantstudy.business.utils import AliasDecoder


@pytest.mark.parametrize("alias,expected_call", [("@links_series/a/b", "links_series")])
def test_alias_decoder_decode(alias: str, expected_call: str) -> None:
    with patch.object(AliasDecoder, expected_call) as mocked_method:
        AliasDecoder.decode(alias, study_version=Mock())
        mocked_method.assert_called_once()


def test_alias_decoder_decode_raises_error() -> None:
    with pytest.raises(NotImplementedError):
        AliasDecoder.decode("@non_existent_alias", study_version=Mock())


def test_alias_decoder_links_series() -> None:
    area_from = "a"
    area_to = "b"
    alias = f"@links_series/{area_from}/{area_to}"

    assert AliasDecoder.links_series(alias, STUDY_VERSION_8) == f"input/links/{area_from}/{area_to}"
    assert AliasDecoder.links_series(alias, STUDY_VERSION_8_3) == f"input/links/{area_from}/{area_to}_parameters"
