from jsonschema import Draft7Validator

from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import (
    IniWriter,
)
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


class InputAreasSets(IniFileNode):
    """
    [all areas]
    caption = All areas
    comments = Spatial aggregates on all areas
    output = false
    apply-filter = add-all
    + = hello
    + = bonjour
    """

    jsonschema_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "caption": {"type": "string"},
                    "comments": {"type": "string"},
                    "output": {"type": "boolean"},
                    "apply-filter": {
                        "type": "string",
                        "enum": ["add-all", "remove-all"],
                    },
                    "+": {"type": "array", "items": {"type": "string"}},
                    "-": {"type": "array", "items": {"type": "string"}},
                },
            },
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self,
            context,
            config,
            validator=InputAreasSets.jsonschema_validator,
            reader=MultipleSameKeysIniReader(["+", "-"]),
            writer=IniWriter(special_keys=["+", "-"]),
        )
