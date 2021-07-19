from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputMiscGenArea(InputSeriesMatrix):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super(InputMiscGenArea, self).__init__(context, config)
