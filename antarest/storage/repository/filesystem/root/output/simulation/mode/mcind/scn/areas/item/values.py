from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
)
from antarest.storage.repository.filesystem.matrix.head_writer import (
    AreaHeadWriter,
)
from antarest.storage.repository.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


class OutputSimulationModeMcIndScnAreasItemValues(OutputSeriesMatrix):
    def __init__(
        self, context: ContextServer, config: StudyConfig, freq: str, area: str
    ):
        super(OutputSimulationModeMcIndScnAreasItemValues, self).__init__(
            context=context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, area),
            head_writer=AreaHeadWriter(area, freq),
            freq=freq,
        )
