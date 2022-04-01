from jsonschema import Draft7Validator

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)


class StudyAntares(IniFileNode):
    """
    study.antares files

    Examples
    --------
    [antares]
    version = 700
    caption = STA-mini
    created = 1480683452
    lastsave = 1602678639
    author = Andrea SGATTONI

    """

    json_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "antares": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "version": {"type": "integer", "minimum": 0},
                        "caption": {"type": "string"},
                        "created": {"type": "number", "minimum": 0},
                        "lastsave": {"type": "number", "minimum": 0},
                        "author": {"type": "string"},
                    },
                    "required": [
                        "version",
                        "caption",
                        "created",
                        "lastsave",
                        "author",
                    ],
                }
            },
            "required": ["antares"],
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=StudyAntares.json_validator
        )
