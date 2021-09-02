from typing import Optional

from antarest.matrixstore.service import MatrixService
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)


class CommandContext:
    def __init__(
        self,
        generator_matrix_constants: Optional[GeneratorMatrixConstants] = None,
        matrix_service: Optional[MatrixService] = None,
    ):
        self.generator_matrix_constants = generator_matrix_constants
        self.matrix_service = matrix_service
