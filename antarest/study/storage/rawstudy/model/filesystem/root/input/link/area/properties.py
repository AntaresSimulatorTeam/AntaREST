from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.ini_file_node import IniFileNode


class InputLinkAreaProperties(IniFileNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        section = {
            "hurdles-cost": bool,
            "loop-flow": bool,
            "use-phase-shifter": bool,
            "transmission-capacities": str,
            "asset-type": str,
            "link-style": str,
            "link-width": int,
            "colorr": int,
            "colorg": int,
            "colorb": int,
            "display-comments": bool,
            "filter-synthesis": str,
            "filter-year-by-year": str,
        }

        types = {link: section for link in config.get_links(area)}
        IniFileNode.__init__(self, context, config, types)
