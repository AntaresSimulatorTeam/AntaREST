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
