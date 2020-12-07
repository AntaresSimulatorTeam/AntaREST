from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def __init__(self, config: Config):
        children = {
            a: InputLinkArea(config.next_file(a), area=a)
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
