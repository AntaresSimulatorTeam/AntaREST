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
import os
import tempfile
import typing as t
from io import BytesIO

import pandas as pd
import pyarrow as pa
from pyarrow import feather
from pyarrow.feather import write_feather


def dataframe_to_bytes(df: pd.DataFrame, metadata: t.Optional[t.Dict[str | bytes, str | bytes]]) -> bytes:
    table: pa.Table = pa.Table.from_pandas(df, preserve_index=False)

    if metadata:
        metadata_bytes = {str(k): str(v) for k, v in metadata.items()}
        schema_metadata: t.Dict[str | bytes, str | bytes] = {k: v for k, v in metadata_bytes.items()}
        table = table.replace_schema_metadata(schema_metadata)

    buffer = BytesIO()
    write_feather(df=table, dest=buffer)  # type:ignore

    return buffer.getvalue()


def bytes_to_dataframe(buffer: bytes) -> pd.DataFrame:
    data = BytesIO(buffer)
    table = feather.read_table(data)

    df = table.to_pandas()

    metadata = table.schema.metadata
    if metadata:
        df.metadata = {k.decode("utf8"): v.decode("utf8") for k, v in metadata.items()}

    return df
