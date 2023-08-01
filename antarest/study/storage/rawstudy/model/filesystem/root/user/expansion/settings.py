from antarest.study.storage.rawstudy.io.reader.ini_reader import (
    SimpleKeyValueReader,
)
from antarest.study.storage.rawstudy.io.writer.ini_writer import (
    SimpleKeyValueWriter,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)


# noinspection SpellCheckingInspection
class ExpansionSettings(IniFileNode):
    # /!\ The name of all the parameters is correct.
    # Especially the differences of "_" and "-" in parameter names.
    """
    Common:
        - optimality_gap: float = 1
        - max_iteration: int = +Inf
        - uc_type: str = "expansion_fast" or "expansion_accurate". default="expansion_fast"
        - master: str = "integer" or "relaxed". default="integer"
        - yearly-weights: str = filename. default = None
        - additional-constraints: str = filename. default = None

    version < 800 only:
        - relaxed-optimality-gap: float = 1e6
        - cut-type: str = "average", "yearly" or "weekly". default="yearly"
        - ampl.solver: str = "cbc"
        - ampl.presolve: int = 0
        - ampl.solve_bounds_frequency: int = 1000000

    version >= 800 only:
        - relative_gap: float = 1e-12
        - solver: str = "Cbc" or "Coin". default="Cbc"
        - batch_size: int = 0
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        common_types = {
            "optimality_gap": float,
            "max_iteration": int,
            "uc_type": str,
            "master": str,
            "yearly-weights": str,
            "additional_constraints": str,
        }
        if config.version < 800:
            types = {
                "relaxed-optimality-gap": float,
                "cut-type": str,
                "ampl.solver": str,
                "ampl.presolve": int,
                "ampl.solve_bounds_frequency": int,
                **common_types,
            }
        else:
            types = {
                "relative-gap": float,
                "solver": str,
                "batch_size": int,
                **common_types,
            }
        super().__init__(
            context,
            config,
            types=types,
            reader=SimpleKeyValueReader(),
            writer=SimpleKeyValueWriter(),
        )
