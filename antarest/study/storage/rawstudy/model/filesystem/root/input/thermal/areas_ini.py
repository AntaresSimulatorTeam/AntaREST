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


class InputThermalAreasIni(IniFileNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        sections = {
            "type": "object",
            "properties": {a: {"type": "number"} for a in config.area_names()},
        }
        schema = {
            "type": "object",
            "properties": {
                "unserverdenergycost": sections,
                "spilledenergycost": sections,
            },
            "additionalProperties": False,
            "required": ["unserverdenergycost", "spilledenergycost"],
        }
        IniFileNode.__init__(
            self, context, config, validator=Draft7Validator(schema)
        )
