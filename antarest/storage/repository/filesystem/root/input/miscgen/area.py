from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


class InputMiscGenArea(InputSeriesMatrix):
    def __init__(self, context: ContextServer, config: StudyConfig):
        super(InputMiscGenArea, self).__init__(context, config)
