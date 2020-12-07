from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.areas.areas import InputAreas
from api_iso_antares.domain.study.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from api_iso_antares.domain.study.root.input.hydro.hydro import InputHydro
from api_iso_antares.domain.study.root.input.link.link import InputLink


class Input(FolderNode):
    def __init__(self, config: Config):
        children = {
            "areas": InputAreas(config.next_file("areas")),
            "bindingconstraints": BindingConstraints(
                config.next_file("bindingconstraints")
            ),
            "hydro": InputHydro(config.next_file("hydro")),
            "links": InputLink(config.next_file("links")),
        }
        FolderNode.__init__(self, children)
