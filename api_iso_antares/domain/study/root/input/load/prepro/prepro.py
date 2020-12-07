from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.load.prepro.area.area import (
    InputLoadPreproArea,
)
from api_iso_antares.domain.study.root.input.load.prepro.correlation import (
    InputLoadPreproCorrelation,
)


class InputLoadPrepro(FolderNode):
    def __init__(self, config: Config):
        children = {
            a: InputLoadPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputLoadPreproCorrelation(
            config.next_file("correlation.ini")
        )
        FolderNode.__init__(self, children)
