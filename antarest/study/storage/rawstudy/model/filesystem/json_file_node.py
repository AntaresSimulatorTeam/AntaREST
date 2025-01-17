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

import json
import typing as t
from pathlib import Path

from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.serialization import from_json, to_json
from antarest.study.storage.rawstudy.ini_reader import IReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class JsonReader(IReader):
    """
    JSON file reader.
    """

    @override
    def read(self, path: t.Any, **kwargs: t.Any) -> JSON:
        content: t.Union[str, bytes]

        if isinstance(path, (Path, str)):
            try:
                with open(path, mode="r", encoding="utf-8") as f:
                    content = f.read()
            except FileNotFoundError:
                # If the file is missing, an empty dictionary is returned,
                # to mimic the behavior of `configparser.ConfigParser`.
                return {}

        elif hasattr(path, "read"):
            with path:
                content = path.read()

        else:  # pragma: no cover
            raise TypeError(repr(type(path)))

        try:
            return t.cast(JSON, from_json(content))
        except json.JSONDecodeError as exc:
            err_msg = f"Failed to parse JSON file '{path}'"
            raise ValueError(err_msg) from exc


class JsonWriter(IniWriter):
    """
    JSON file writer.
    """

    @override
    def write(self, data: JSON, path: Path) -> None:
        with open(path, "wb") as fh:
            fh.write(to_json(data))


class JsonFileNode(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        super().__init__(context, config, types, JsonReader(), JsonWriter())
