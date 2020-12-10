from api_iso_antares.custom_types import JSON
from api_iso_antares.engine.swagger.nodes import RootNode


class SwaggerEngine:
    @staticmethod
    def parse(jsm) -> JSON:
        return SwaggerEngine._build(jsm)

    @staticmethod
    def _build(jsm) -> JSON:
        root_node = RootNode(jsm=jsm)
        return root_node.get_content()
