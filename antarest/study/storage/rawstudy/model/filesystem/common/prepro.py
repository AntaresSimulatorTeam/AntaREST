from jsonschema import Draft7Validator

from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
    DEFAULT_INI_VALIDATOR,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class PreproCorrelation(IniFileNode):
    json_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "general": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["monthly", "annual", ""],
                        },
                    },
                },
                "annual": {"$ref": "#/$defs/correlation"},
                "0": {"$ref": "#/$defs/correlation"},
                "1": {"$ref": "#/$defs/correlation"},
                "2": {"$ref": "#/$defs/correlation"},
                "3": {"$ref": "#/$defs/correlation"},
                "4": {"$ref": "#/$defs/correlation"},
                "5": {"$ref": "#/$defs/correlation"},
                "6": {"$ref": "#/$defs/correlation"},
                "7": {"$ref": "#/$defs/correlation"},
                "8": {"$ref": "#/$defs/correlation"},
                "9": {"$ref": "#/$defs/correlation"},
                "10": {"$ref": "#/$defs/correlation"},
                "11": {"$ref": "#/$defs/correlation"},
            },
            "$defs": {
                "correlation": {
                    "type": "object",
                    "patternProperties": {".*%.*": {"type": "number"}},
                }
            },
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self, context, config, validator=PreproCorrelation.json_validator
        )


class PreproAreaSettings(IniFileNode):
    json_schema_validator = Draft7Validator(
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "general": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "distribution": {
                            "type": "string",
                            "enum": [
                                "unknown",
                                "Uniform",
                                "Beta",
                                "Normal",
                                "WeibullShapeA",
                                "GammaShapeA",
                            ],
                        },
                        "capacity": {"type": "number", "minimum": 0},
                        "conversion": {"type": "boolean"},
                        "translation": {
                            "type": "string",
                            "enum": [
                                "never",
                                "before-conversion",
                                "after-conversion",
                            ],
                        },
                    },
                }
            },
        }
    )

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        IniFileNode.__init__(
            self,
            context,
            config,
            validator=PreproAreaSettings.json_schema_validator,
        )


class PreproArea(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "conversion": InputSeriesMatrix(
                self.context, self.config.next_file("conversion.txt")
            ),
            "data": InputSeriesMatrix(
                self.context, self.config.next_file("data.txt")
            ),
            "k": InputSeriesMatrix(
                self.context, self.config.next_file("k.txt")
            ),
            "translation": InputSeriesMatrix(
                self.context, self.config.next_file("translation.txt")
            ),
            "settings": PreproAreaSettings(
                self.context, self.config.next_file("settings.ini")
            ),
        }
        return children


class InputPrepro(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: PreproArea(self.context, self.config.next_file(a))
            for a in self.config.area_names()
        }
        children["correlation"] = PreproCorrelation(
            self.context, self.config.next_file("correlation.ini")
        )
        return children
