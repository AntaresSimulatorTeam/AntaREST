from typing import Optional

from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)


class CommandContext:
    def __init__(
        self,
        generator_matrix_constants: Optional[GeneratorMatrixConstants] = None,
    ):
        self.generator_matrix_constants = generator_matrix_constants
