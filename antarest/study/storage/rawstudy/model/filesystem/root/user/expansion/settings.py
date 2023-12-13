from antarest.study.storage.rawstudy.ini_reader import SimpleKeyValueReader
from antarest.study.storage.rawstudy.ini_writer import SimpleKeyValueWriter
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


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
        - relaxed-optimality-gap: float = 0.001  # relaxed-optimality-gap > 0
        - cut-type: str = "average", "yearly" or "weekly". default="yearly"
        - ampl.solver: str = "cbc"
        - ampl.presolve: int = 0
        - ampl.solve_bounds_frequency: int = 1000000

    version >= 800 only:
        - relative_gap: float = 1e-12
        - solver: str = "Cbc", "Coin" or "Xpress". default="Cbc"
        - batch_size: int = 0
        - separation_parameter: float = 0.5  # 0 <= separation_parameter <= 1
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
                "relaxed_optimality_gap": float,
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
                "separation_parameter": float,
                **common_types,
            }
        super().__init__(
            context,
            config,
            types=types,
            reader=SimpleKeyValueReader(),
            writer=SimpleKeyValueWriter(),
        )
