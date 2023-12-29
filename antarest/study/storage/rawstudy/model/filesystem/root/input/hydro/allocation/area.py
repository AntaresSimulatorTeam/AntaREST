from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputHydroAllocationArea(IniFileNode):
    """
    This class can read the `input/hydro/allocation/foo_area.ini`.
    """

    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        types = {"[allocation]": {area: int}}
        super().__init__(context, config, types, reader=IniReader())
