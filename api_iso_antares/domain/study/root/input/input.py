from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.areas.areas import InputAreas


class Input(FolderNode):
    def __init__(self, config: Config):
        children = {"areas": InputAreas(config.next_file("areas"))}
        FolderNode.__init__(self, children)
