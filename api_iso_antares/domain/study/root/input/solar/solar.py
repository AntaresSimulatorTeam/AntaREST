from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.solar.prepro.prepro import (
    InputSolarPrepro,
)
from api_iso_antares.domain.study.root.input.solar.series.series import (
    InputSolarSeries,
)


class InputSolar(FolderNode):
    def __init__(self, config: Config):
        children = {
            "prepro": InputSolarPrepro(config.next_file("prepro")),
            "series": InputSolarSeries(config.next_file("series")),
        }
        FolderNode.__init__(self, children)
