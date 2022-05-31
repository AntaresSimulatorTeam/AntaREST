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


class LayersIni(IniFileNode):
    """
    Examples
    -------
    [layers]
    0 = All
    1 = Map 1
    [activeLayer]
    activeLayerID = 0
    showAllLayer = true
    """

    schema_validator = Draft7Validator(
        {
            "type": "object",
            "properties": {
                "layers": {
                    "type": "object",
                    "patternProperties": {"\\d+": {"type": "string"}},
                },
                "activeLayer": {
                    "type": "object",
                    "properties": {
                        "activeLayerID": {"type": "integer"},
                        "showAllLayer": {"type": "boolean"},
                    },
                },
            },
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=LayersIni.schema_validator
        )
