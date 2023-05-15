from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputShortTermStorageAreaList(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        # The list.ini file contains one section per short-term storage object associated to the area.
        # Every section contains the following properties :
        # - a name (str)
        # - a group (Possible values: "PSP_open", "PSP_closed", "Pondage", "Battery", "Other_1", ..., "Other_5", default = Other_1)
        # - an efficiency coefficient (double in range 0-1)
        # - a reservoir capacity (double > 0)
        # - an initial level (double in range 0-1)
        # - a withdrawal nominal capacity (double in range 0-1)
        # - an injection nominal capacity (double in range 0-1)
        # - a storage cycle (int in range 24-268)
        types = {
            st_storage: dict
            for st_storage in config.get_short_term_storage_names(area)
        }
        super().__init__(context, config, types)
