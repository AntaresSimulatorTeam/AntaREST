from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.thermal.area_ini import (
    InputThermalAreaIni,
)
from api_iso_antares.domain.study.root.input.thermal.cluster.cluster import (
    InputThermalClusters,
)
from api_iso_antares.domain.study.root.input.thermal.prepro.prepro import (
    InputThermalPrepro,
)
from api_iso_antares.domain.study.root.input.thermal.series.series import (
    InputThermalSeries,
)


class InputThermal(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "clusters": InputThermalClusters(config.next_file("clusters")),
            "prepro": InputThermalPrepro(config.next_file("prepro")),
            "series": InputThermalSeries(config.next_file("series")),
            "area": InputThermalAreaIni(config.next_file("areas.ini")),
        }
        FolderNode.__init__(self, children)
