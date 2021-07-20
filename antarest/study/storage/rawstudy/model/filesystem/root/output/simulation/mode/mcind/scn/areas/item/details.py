from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.head_writer import (
    AreaHeadWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


class OutputSimulationModeMcIndScnAreasItemDetails(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
        area: str,
    ):
        super(OutputSimulationModeMcIndScnAreasItemDetails, self).__init__(
            context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, area),
            head_writer=AreaHeadWriter(area, freq),
            freq=freq,
        )
