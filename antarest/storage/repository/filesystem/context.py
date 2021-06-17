from dataclasses import dataclass

from antarest.matrixstore.service import MatrixService


@dataclass
class ContextServer:
    matrix: MatrixService
