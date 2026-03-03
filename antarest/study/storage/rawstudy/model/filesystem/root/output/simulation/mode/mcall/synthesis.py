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

from typing import List, Optional

import pandas as pd
from typing_extensions import override

from antarest.core.exceptions import MustNotModifyOutputException
from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.lazy_node import LazyNode


class OutputSynthesis(LazyNode[JSON, bytes, bytes]):
    @override
    def get_lazy_content(self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False) -> str:
        return f"matrix://{self.config.path.name}"  # prefix used by the front to parse the back-end response

    @override
    def load(
        self, url: Optional[List[str]] = None, depth: int = -1, expanded: bool = False, formatted: bool = True
    ) -> JSON:
        file_path = self.config.path
        df = pd.read_csv(file_path, sep="\t")
        return df.to_dict(orient="split", index=False)

    @override
    def dump(self, data: bytes, url: Optional[List[str]] = None) -> None:
        raise MustNotModifyOutputException(self.config.path.name)
