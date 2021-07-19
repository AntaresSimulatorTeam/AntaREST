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
    LinkHeadWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)


class OutputSimulationModeMcAllLinksItemValues(OutputSeriesMatrix):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        freq: str,
        src: str,
        dest: str,
    ):
        super(OutputSimulationModeMcAllLinksItemValues, self).__init__(
            context=context,
            config=config,
            date_serializer=FactoryDateSerializer.create(freq, src),
            head_writer=LinkHeadWriter(src, dest, freq),
            freq=freq,
        )
