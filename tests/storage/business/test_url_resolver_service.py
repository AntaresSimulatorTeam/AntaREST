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

from unittest.mock import Mock

import pandas as pd

from antarest.matrixstore.uri_resolver_service import UriResolverService

MOCK_MATRIX = pd.DataFrame(data=[[1, 2], [3, 4]], index=["1", "2"], columns=["a", "b"])


def test_build_matrix_uri():
    resolver = UriResolverService(matrix_service=Mock())
    assert "matrix://my-id" == resolver.build_matrix_uri("my-id")


def test_resolve_matrix():
    matrix_service = Mock()
    matrix_service.get.return_value = pd.DataFrame(index=["1", "2"], columns=["a", "b"], data=[[1, 2], [3, 4]])

    resolver = UriResolverService(matrix_service=matrix_service)

    assert resolver.get_matrix("matrix://my-id").equals(MOCK_MATRIX)
    matrix_service.get.assert_called_once_with("my-id")
