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


class InputAreasUi(IniFileNode):
    """
    Examples
    --------
    [ui]
    x = 1
    y = 135
    color_r = 0
    color_g = 128
    color_b = 255
    layers = 0
    [layerX]
    0 = 1

    [layerY]
    0 = 135

    [layerColor]
    0 = 0 , 128 , 255
    """

    json_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ui": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "color_r": {"type": "number"},
                        "color_g": {"type": "number"},
                        "color_b": {"type": "number"},
                        "layers": {"type": ["number", "string"]},
                    },
                    "required": [
                        "x",
                        "y",
                        "color_r",
                        "color_g",
                        "color_b",
                        "layers",
                    ],
                },
                "layerX": {
                    "type": "object",
                    "patternProperties": {"\\d+": {"type": "number"}},
                    "additionalProperties": False,
                },
                "layerY": {
                    "type": "object",
                    "patternProperties": {"\\d+": {"type": "number"}},
                    "additionalProperties": False,
                },
                "layerColor": {
                    "type": "object",
                    "patternProperties": {"\\d+": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
            "required": ["ui", "layerX", "layerY", "layerColor"],
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=InputAreasUi.json_validator
        )
