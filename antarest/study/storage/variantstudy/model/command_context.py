from dataclasses import dataclass

from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)


@dataclass
class CommandContext:
    generator_matrix_constants: GeneratorMatrixConstants
