from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.storage.repository.filesystem.raw_file_node import RawFileNode


class InputLoadSeriesArea(InputSeriesMatrix):
    def __init__(self, config: StudyConfig):
        super(InputLoadSeriesArea, self).__init__(config)
