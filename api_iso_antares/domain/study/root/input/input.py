from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.areas.areas import InputAreas
from api_iso_antares.domain.study.root.input.bindingconstraints.bindingcontraints import (
    BindingConstraints,
)
from api_iso_antares.domain.study.root.input.hydro.hydro import InputHydro
from api_iso_antares.domain.study.root.input.link.link import InputLink
from api_iso_antares.domain.study.root.input.load.load import InputLoad


class Input(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "areas": InputAreas(config.next_file("areas")),
            "bindingconstraints": BindingConstraints(
                config.next_file("bindingconstraints")
            ),
            "hydro": InputHydro(config.next_file("hydro")),
            "links": InputLink(config.next_file("links")),
            "load": InputLoad(config.next_file("load")),
        }
        FolderNode.__init__(self, children)
