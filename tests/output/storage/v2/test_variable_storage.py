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
from polars.testing import assert_frame_equal

from antarest.output.filestudy.model import OutputDataFrame, VariableDescription
from antarest.output.storage.v2.variables_storage import _adapt_df


def test_adapt_df_to_columns() -> None:
    columns = [
        VariableDescription("var1", None, None),
        VariableDescription("var2", None, None),
        VariableDescription("var3", None, None),
    ]
    output_df = OutputDataFrame(
        data=pl.DataFrame(
            [
                pl.Series(name="1", values=[0, 1], dtype=pl.Float64()),
                pl.Series(name="2", values=[2, 3], dtype=pl.Float64()),
            ]
        ),
        headers=[VariableDescription("var3", None, None), VariableDescription("var1", None, None)],
    )
    adapted_df = _adapt_df(columns, output_df)

    # we expect to have second input column in 1st position (var1), then a null column for var2,
    # then 1st input column in 3rd position for var3
    expected_df = pl.DataFrame(
        [
            pl.Series(name="0", values=[2, 3], dtype=pl.Float64()),
            pl.Series(name="1", values=[None, None], dtype=pl.Float64()),
            pl.Series(name="2", values=[0, 1], dtype=pl.Float64()),
        ]
    )

    assert_frame_equal(adapted_df, expected_df)
