import json
from pathlib import Path
from typing import Any, Dict, Optional, cast

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.ini_reader import IReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class JsonReader(IReader):
    def read(self, path: Any) -> JSON:
        if isinstance(path, Path):
            return cast(JSON, json.loads(path.read_text(encoding="utf-8")))
        return cast(JSON, json.loads(path))


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
