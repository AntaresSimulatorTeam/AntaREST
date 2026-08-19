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
import polars as pl
import pytest

from antarest.output.filestudy.model import OutputDataFrame


def test_output_df_should_raise_when_wrong_headers_count() -> None:

    df = pl.DataFrame(data=[[0, 1], [2, 3]], schema=["1", "2"])
    with pytest.raises(ValueError):
        OutputDataFrame(data=df, headers=("col1"))

    output_df = OutputDataFrame(data=df, headers=("col1", "col2"))
    assert output_df.headers == ("col1", "col2")
