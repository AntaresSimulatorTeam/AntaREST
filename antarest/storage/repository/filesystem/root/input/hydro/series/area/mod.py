from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputHydroSeriesAreaMod(InputSeriesMatrix):
    def __init__(self, config: StudyConfig):
        InputSeriesMatrix.__init__(self, config)
