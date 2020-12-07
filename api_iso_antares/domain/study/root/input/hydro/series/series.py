from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.hydro.series.area.area import (
    InputHydroSeriesArea,
)


class InputHydroSeries(FolderNode):
    def __init__(self, config: Config):
        children = {
            a: InputHydroSeriesArea(config.next_file(a))
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
