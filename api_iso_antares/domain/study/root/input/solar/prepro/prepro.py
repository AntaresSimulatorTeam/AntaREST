from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.solar.prepro.area.area import (
    InputSolarPreproArea,
)
from api_iso_antares.domain.study.root.input.solar.prepro.correlation import (
    InputSolarPreproCorrelation,
)


class InputSolarPrepro(FolderNode):
    def __init__(self, config: Config):
        children = {
            a: InputSolarPreproArea(config.next_file(a))
            for a in config.area_names
        }
        children["correlation"] = InputSolarPreproCorrelation(
            config.next_file("correlation.ini")
        )
        FolderNode.__init__(self, children)
