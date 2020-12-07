from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.default_node import DefaultNode
from api_iso_antares.domain.study.root.layers.layer_ini import LayersIni


class Layers(DefaultNode):
    def __init__(self, config: Config):
        children = {"layers": LayersIni(config.next_file("layers.ini"))}
        DefaultNode.__init__(self, children)
