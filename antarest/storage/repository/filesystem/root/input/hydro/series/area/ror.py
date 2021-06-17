from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputHydroSeriesAreaRor(InputSeriesMatrix):
    def __init__(self, context: ContextServer, config: StudyConfig):
        super(InputHydroSeriesAreaRor, self).__init__(self.context, config)
