from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.root.input.load.prepro.prepro import (
    InputLoadPrepro,
)
from api_iso_antares.filesystem.root.input.load.series.series import (
    InputLoadSeries,
)


class InputLoad(FolderNode):
    def __init__(self, config: Config):
        children = {
            "prepro": InputLoadPrepro(config.next_file("prepro")),
            "series": InputLoadSeries(config.next_file("series")),
        }
        FolderNode.__init__(self, children)
