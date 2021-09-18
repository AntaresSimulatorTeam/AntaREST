from pydantic import BaseModel

from antarest.matrixstore.service import MatrixService, ISimpleMatrixService
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)


class CommandContext(BaseModel):
    generator_matrix_constants: GeneratorMatrixConstants
    matrix_service: ISimpleMatrixService
    patch_service: PatchService

    class Config:
        arbitrary_types_allowed = True
