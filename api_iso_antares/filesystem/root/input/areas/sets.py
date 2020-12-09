from api_iso_antares.antares_io.reader import SetsIniReader
from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.ini_file_node import IniFileNode


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
        # TODO implemented pattern strategy with injection inside IniFileMode for reader and writer.
        # TODO Implements writer sets.ini
        IniFileNode.__init__(self, config, types={})
