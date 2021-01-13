import configparser
from pathlib import Path
from typing import List, Optional, Union, cast, Type, Dict, Any

from api_iso_antares.antares_io.reader import IniReader
from api_iso_antares.antares_io.reader.ini_reader import IReader
from api_iso_antares.antares_io.writer.ini_writer import IniWriter
from api_iso_antares.custom_types import JSON, SUB_JSON
from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.inode import INode, TREE


class IniReaderError(Exception):
    def __init__(self, name: str, mes: str):
        super(IniReaderError, self).__init__(f"Error read node {name} = {mes}")


class IniFileNode(INode[SUB_JSON, SUB_JSON, JSON]):
    def __init__(
        self,
        config: Config,
        types: Dict[str, Any],
        reader: Optional[IReader] = None,
    ):
        self.path = config.path
        self.types = types
        self.reader = reader or IniReader()
        self.writer = IniWriter()

    def build(self, config: Config) -> TREE:
        pass  # end node has nothing to build

    def get(
        self, url: Optional[List[str]] = None, depth: int = -1
    ) -> SUB_JSON:
        if depth == 0:
            return {}
        url = url or []
        try:
            json = self.reader.read(self.path)
        except Exception as e:
            raise IniReaderError(self.__class__.__name__, str(e))
        # TODO self.validate(json)
        if len(url) == 2:
            json = json[url[0]][url[1]]
        elif len(url) == 1:
            json = json[url[0]]
        else:
            json = {k: {} for k in json} if depth == 1 else json
        return cast(SUB_JSON, json)

    def save(self, data: SUB_JSON, url: Optional[List[str]] = None) -> None:
        url = url or []
        json = self.reader.read(self.path) if self.path.exists() else {}
        if len(url) == 2:
            json[url[0]][url[1]] = data
        elif len(url) == 1:
            json[url[0]] = data
        else:
            json = cast(JSON, data)
        # TODO self.validate(json)
        self.writer.write(json, self.path)

    def validate(self, data: JSON) -> None:
        for section, params in self.types.items():
            if section not in data:
                raise ValueError(
                    f"section {section} not in {self.__class__.__name__}"
                )
            self._validate_param(section, params, data[section])

    def _validate_param(self, section: str, params: Any, data: JSON) -> None:
        for param, typing in params.items():
            if param not in data:
                raise ValueError(
                    f"param {param} of section {section} not in {self.__class__.__name__}"
                )
            if not isinstance(data[param], typing):
                raise ValueError(
                    f"param {param} of section {section} in {self.__class__.__name__} bad type"
                )
