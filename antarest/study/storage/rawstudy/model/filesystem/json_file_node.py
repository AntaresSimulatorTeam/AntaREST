import json
import typing as t
from pathlib import Path

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.ini_reader import IReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class JsonReader(IReader):
    """
    JSON file reader.
    """

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
            return t.cast(JSON, json.loads(content))
        except json.JSONDecodeError as exc:
            err_msg = f"Failed to parse JSON file '{path}'"
            raise ValueError(err_msg) from exc


class JsonWriter(IniWriter):
    """
    JSON file writer.
    """

    def write(self, data: JSON, path: Path) -> None:
        with open(path, "w") as fh:
            json.dump(data, fh)


class JsonFileNode(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        types: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        super().__init__(context, config, types, JsonReader(), JsonWriter())
