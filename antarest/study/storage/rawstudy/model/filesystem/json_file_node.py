import json
from pathlib import Path
from typing import Optional, Dict, Any, cast

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.io.reader.ini_reader import IReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class JsonReader(IReader):
    def read(self, path: Path) -> JSON:
        with open(path, "r") as fh:
            return cast(JSON, json.load(fh))


class JsonWriter(IniWriter):
    def write(self, data: JSON, path: Path) -> None:
        with open(path, "w") as fh:
            json.dump(data, fh)


class JsonFileNode(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(context, config, types, JsonReader(), JsonWriter())
