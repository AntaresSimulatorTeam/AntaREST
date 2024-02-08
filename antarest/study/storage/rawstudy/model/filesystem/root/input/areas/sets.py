from antarest.study.storage.rawstudy.ini_reader import IniReader
from antarest.study.storage.rawstudy.ini_writer import IniWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


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
        IniFileNode.__init__(
            self,
            context,
            config,
            types={},
            reader=IniReader(["+", "-"]),
            writer=IniWriter(special_keys=["+", "-"]),
        )
