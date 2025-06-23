from datetime import datetime

from antarest.core.serde import AntaresBaseModel


class MatrixModel(AntaresBaseModel, extra="forbid", populate_by_name=True):
    id: str
    width: int
    height: int
    created_at: datetime
    version: int
