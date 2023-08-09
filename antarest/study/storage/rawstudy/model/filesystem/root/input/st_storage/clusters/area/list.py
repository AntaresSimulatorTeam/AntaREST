from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputSTStorageAreaList(IniFileNode):
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
        # - an initial_level_optim (bool, default = False)
        # - a withdrawal nominal capacity (double > 0)
        # - an injection nominal capacity (double > 0)
        types = {
            st_storage_id: dict
            for st_storage_id in config.get_st_storage_ids(area)
        }
        super().__init__(context, config, types)
