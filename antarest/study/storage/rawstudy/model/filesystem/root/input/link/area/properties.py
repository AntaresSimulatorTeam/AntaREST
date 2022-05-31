from typing import Dict, Any

from jsonschema import Draft7Validator

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
        link_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "hurdles-cost": {"type": "boolean"},
                "transmission-capacities": {"type": "string"},
                "display-comments": {"type": "boolean"},
                "filter-synthesis": {"type": "string"},
                "filter-year-by-year": {"type": "string"},
            },
        }

        if config.version >= 650:
            link_schema["properties"]["loop-flow"] = {"type": "boolean"}
            link_schema["properties"]["use-phase-shifter"] = {
                "type": "boolean"
            }
            link_schema["properties"]["asset-type"] = {"type": "string"}
            link_schema["properties"]["link-style"] = {"type": "string"}
            link_schema["properties"]["link-width"] = {"type": "number"}
            link_schema["properties"]["colorr"] = {"type": "number"}
            link_schema["properties"]["colorg"] = {"type": "number"}
            link_schema["properties"]["colorb"] = {"type": "number"}

        schema = {
            "type": "object",
            "properties": {
                link: link_schema for link in config.get_links(area)
            },
        }
        IniFileNode.__init__(
            self, context, config, validator=Draft7Validator(schema)
        )
