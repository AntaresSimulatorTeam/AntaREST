from pydantic import BaseModel

from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)


class CommandContext(BaseModel):
    generator_matrix_constants: GeneratorMatrixConstants

    class Config:
        arbitrary_types_allowed = True
