from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from api_iso_antares.domain.study.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def __init__(self, config: Config):
        children = {
            "prepro": InputWindPrepro(config.next_file("prepro")),
            "series": InputWindSeries(config.next_file("series")),
        }
        FolderNode.__init__(self, children)
