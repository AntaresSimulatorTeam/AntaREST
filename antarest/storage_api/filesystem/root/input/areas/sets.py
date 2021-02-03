from antarest.storage_api.antares_io.reader import SetsIniReader
from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.ini_file_node import IniFileNode


class InputAreasSets(IniFileNode):
    """
    [all areas]
    caption = All areas
    comments = Spatial aggregates on all areas
    output = false
    apply-filter = add-all
    + = hello
    + = bonjour
    """

    def __init__(self, config: StudyConfig):
        # TODO Implements writer sets.ini
        IniFileNode.__init__(self, config, types={}, reader=SetsIniReader())
