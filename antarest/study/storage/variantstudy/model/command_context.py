from typing import Optional

from pydantic import BaseModel

from antarest.matrixstore.service import MatrixService, ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.model.interfaces import (
    ICommandExtractor,
)


class CommandContext(BaseModel):
    generator_matrix_constants: GeneratorMatrixConstants
    matrix_service: ISimpleMatrixService
    patch_service: PatchService
    command_extractor: Optional[ICommandExtractor] = None  # used in tests

    class Config:
        arbitrary_types_allowed = True
