from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.wind.prepro.area.area import (
    InputWindPreproArea,
)
from api_iso_antares.domain.study.root.input.wind.prepro.correlation import (
    InputWindPreproCorrelation,
)


class InputWindPrepro(FolderNode):
    def __init__(self, config: Config):
        children = {
            a: InputWindPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputWindPreproCorrelation(
            config.next_file("correlation.ini")
        )
        FolderNode.__init__(self, children)
