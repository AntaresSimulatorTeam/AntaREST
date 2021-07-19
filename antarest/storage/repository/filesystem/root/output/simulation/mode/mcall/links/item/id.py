from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.matrix.date_serializer import (
    FactoryDateSerializer,
)
from antarest.storage.repository.filesystem.matrix.head_writer import (
    LinkHeadWriter,
)
from antarest.storage.repository.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


class OutputSimulationModeMcAllLinksItemId(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
        src: str,
        dest: str,
    ):
        super(OutputSimulationModeMcAllLinksItemId, self).__init__(
            context=context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, src),
            head_writer=LinkHeadWriter(src, dest, freq),
            freq=freq,
        )
