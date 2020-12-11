from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.root.output.simulation.about.areas import (
    OutputSimulationAboutAreas,
)
from api_iso_antares.filesystem.root.output.simulation.about.comments import (
    OutputSimulationAboutComments,
)
from api_iso_antares.filesystem.root.output.simulation.about.links import (
    OutputSimulationAboutLinks,
)
from api_iso_antares.filesystem.root.output.simulation.about.map import (
    OutputSimulationAboutMap,
)
from api_iso_antares.filesystem.root.output.simulation.about.parameters import (
    OutputSimulationAboutParameters,
)
from api_iso_antares.filesystem.root.output.simulation.about.study import (
    OutputSimulationAboutStudy,
)


class OutputSimulationAbout(FolderNode):
    def __init__(self, config: Config):
        children = {
            "areas": OutputSimulationAboutAreas(config.next_file("areas.txt")),
            "comments": OutputSimulationAboutComments(
                config.next_file("comments.txt")
            ),
            "links": OutputSimulationAboutLinks(config.next_file("links.txt")),
            "map": OutputSimulationAboutMap(config.next_file("map")),
            "study": OutputSimulationAboutStudy(config.next_file("study.ini")),
            "parameters": OutputSimulationAboutParameters(
                config.next_file("parameters.ini")
            ),
        }
        FolderNode.__init__(self, config, children)
