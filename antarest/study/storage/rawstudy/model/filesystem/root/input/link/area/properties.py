from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


class InputLinkAreaProperties(IniFileNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        section = {
            "hurdles-cost": bool,
            "transmission-capacities": str,
            "display-comments": bool,
            "filter-synthesis": str,
            "filter-year-by-year": str,
        }

        if config.version >= 650:
            section["loop-flow"] = bool
            section["use-phase-shifter"] = bool
            section["asset-type"] = str
            section["link-style"] = str
            section["link-width"] = int
            section["colorr"] = int
            section["colorg"] = int
            section["colorb"] = int

        types = {link: section for link in config.get_links(area)}
        IniFileNode.__init__(self, context, config, types)
