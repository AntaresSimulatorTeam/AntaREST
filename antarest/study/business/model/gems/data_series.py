from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.np_array import NpArray


class GemsDataSeries(AntaresBaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", arbitrary_types_allowed=True)

    id: str
    values: NpArray
