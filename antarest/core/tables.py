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
import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Generic, Self, Sequence, TypeVar

import polars as pl
from polars import selectors as cs

DF = TypeVar("DF", pl.DataFrame, pl.LazyFrame)
C = TypeVar("C")


@dataclass(frozen=True)
class Table(Generic[DF, C]):
    """
    Adds columns metadata to a polars dataframe, to better represent them.

    Polars only supports strings as column headers, and does not allow to associate metadata objects to them.
    This class works around that limitation.

    A few operations are available to guarantee consistency between the columns and the data.
    """

    columns: Sequence[C]
    dataframe: DF

    def select(self, predicate: Callable[[C], bool]) -> "Self":
        """
        Selects only columns for which the predicate is true.
        """
        filtered_columns_indices = [k for k, col in enumerate(self.columns) if predicate(col)]
        filtered_columns = [self.columns[k] for k in filtered_columns_indices]
        filtered_matrix = self.dataframe.select(cs.by_index(filtered_columns_indices))
        return dataclasses.replace(self, dataframe=filtered_matrix, columns=filtered_columns)

    def sort_columns(self, sort_key: Callable[[C], Any]) -> "Self":
        """
        Sorts columns according to the given sort key provider.
        """
        sorted_indices = [i for i, col in sorted(enumerate(self.columns), key=lambda tuple: sort_key(tuple[1]))]
        final_columns = [self.columns[c] for c in sorted_indices]
        final_df = self.dataframe.select(cs.by_index(sorted_indices))
        return dataclasses.replace(self, dataframe=final_df, columns=final_columns)

    def to_polars(self, naming: Callable[[C], str]) -> DF:
        """
        Converts to a plain polars frame, you need to provide a function to create unique column names for each col.
        """
        renamings = [cs.by_index(i).alias(naming(col)) for i, col in enumerate(self.columns)]
        return self.dataframe.select(*renamings)


class LazyTable(Table[pl.LazyFrame, C]):
    """
    Specialization for lazy frames, supports conversion to a collected dataframe.
    """

    def collect(self) -> Table[pl.DataFrame, C]:
        """
        Converts the lazy frame to a collected dataframe.
        """
        return Table(dataframe=self.dataframe.collect(), columns=self.columns)
