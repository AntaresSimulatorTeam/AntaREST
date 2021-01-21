from storage_api.antares_io.reader import SetsIniReader
from storage_api.filesystem.config.model import Config
from storage_api.filesystem.ini_file_node import IniFileNode


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

    def __init__(self, config: Config):
        # TODO Implements writer sets.ini
        IniFileNode.__init__(self, config, types={}, reader=SetsIniReader())
