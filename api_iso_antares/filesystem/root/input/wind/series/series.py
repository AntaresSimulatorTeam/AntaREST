from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.root.input.wind.series.area import (
    InputWindSeriesArea,
)


class InputWindSeries(FolderNode):
    def __init__(self, config: Config):
        children = {
            f"wind_{a}": InputWindSeriesArea(config.next_file(f"wind_{a}.txt"))
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
