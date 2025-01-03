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

from abc import ABC, abstractmethod

from typing_extensions import override


class HeadWriter(ABC):
    """
    Abstract head output matrix builder.
    """

    @abstractmethod
    def build(self, var: int, end: int, start: int = 1) -> str:
        """
        Build matrix header.
        Args:
            var: number of variables
            end: time horizon end
            start: time horizon start

        Returns: string header ready to save

        """
        raise NotImplementedError()


class AreaHeadWriter(HeadWriter):
    """
    Implementation for area head matrix.
    """

    def __init__(self, area: str, data_type: str, freq: str):
        self.head = f"""{area.upper()}\tarea\t{data_type}\t{freq}
\tVARIABLES\tBEGIN\tEND
"""

    @override
    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"


class LinkHeadWriter(HeadWriter):
    """
    Implementation for link head matrix
    """

    def __init__(self, src: str, dest: str, freq: str):
        self.head = f"""{src.upper()}\tlink\tva\t{freq}
{dest.upper()}\tVARIABLES\tBEGIN\tEND
"""

    @override
    def build(self, var: int, end: int, start: int = 1) -> str:
        return self.head + f"\t{var}\t{start}\t{end}\n\n"
