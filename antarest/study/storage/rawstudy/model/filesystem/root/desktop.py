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


class Desktop(IniFileNode):
    """
    Desktop.ini file

    Examples
    --------
    [.shellclassinfo]
    iconfile = settings/resources/study.ico
    iconindex = 0
    infotip = Antares Study7.0: STA-mini
    """

    json_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                ".shellclassinfo": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "iconfile": {"type": "string"},
                        "iconindex": {"type": "number"},
                        "infotip": {"type": "string"},
                    },
                    "required": ["iconfile", "iconindex", "infotip"],
                }
            },
            "required": [".shellclassinfo"],
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=Desktop.json_validator
        )
