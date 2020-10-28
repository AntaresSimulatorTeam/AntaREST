from typing import cast

import yaml

from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.nodes import RootNode
from api_iso_antares.jsm import JsonSchema


class SwaggerEngine:
    @staticmethod
    def parse(jsm: JsonSchema) -> JSON:
        return SwaggerEngine._build(jsm)

    @staticmethod
    def _build(jsm: JsonSchema) -> JSON:
        root_node = RootNode(jsm=jsm)
        return root_node.get_content()

    @staticmethod
    def json_to_yaml(data: JSON) -> str:
        return cast(str, yaml.dump(data, default_flow_style=False))

    @staticmethod
    def yaml_to_json(data: str) -> JSON:
        return cast(JSON, yaml.load(data, Loader=yaml.FullLoader))
