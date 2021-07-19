from antarest.storage.business.rawstudy.io.reader import SetsIniReader
from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.ini_file_node import IniFileNode


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

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        # TODO Implements writer sets.ini
        IniFileNode.__init__(
            self, context, config, types={}, reader=SetsIniReader()
        )
