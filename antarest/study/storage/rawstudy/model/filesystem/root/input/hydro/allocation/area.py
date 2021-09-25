from pathlib import Path

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.io.reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class FixedAllocationKeyIniReader(IniReader):
    def read(self, path: Path) -> JSON:
        data: JSON = super().read(path)
        if "[allocation" in data:
            data["[allocation]"] = data["[allocation"]
            del data["[allocation"]
        return data


class InputHydroAllocationArea(IniFileNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        types = {"[allocation]": {area: int}}
        IniFileNode.__init__(
            self, context, config, types, reader=FixedAllocationKeyIniReader()
        )
