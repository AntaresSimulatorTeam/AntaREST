from copy import deepcopy
from typing import Dict, Any

from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.io.writer.ini_writer import (
    IniWriter,
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

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


class GeneralData(IniFileNode):
    TYPES: Dict[str, Dict[str, Any]] = {
        "general": {
            "mode": str,
            "horizon": (int, str),
            "nbyears": int,
            "simulation.start": int,
            "simulation.end": int,
            "january.1st": str,
            "first-month-in-year": str,
            "first.weekday": str,
            "leapyear": bool,
            "year-by-year": bool,
            "derated": bool,
            "custom-ts-numbers": bool,
            "user-playlist": bool,
            "filtering": bool,
            "active-rules-scenario": str,
            "generate": str,
            "nbtimeseriesload": int,
            "nbtimeserieshydro": int,
            "nbtimeserieswind": int,
            "nbtimeseriesthermal": int,
            "nbtimeseriessolar": int,
            "refreshtimeseries": str,
            "intra-modal": str,
            "inter-modal": str,
            "refreshintervalload": int,
            "refreshintervalhydro": int,
            "refreshintervalwind": int,
            "refreshintervalthermal": int,
            "refreshintervalsolar": int,
            "readonly": bool,
        },
        "input": {"import": str},
        "output": {
            "synthesis": bool,
            "storenewset": bool,
            "archives": str,
        },
        "optimization": {
            "simplex-range": str,
            "transmission-capacities": str,
            "include-constraints": bool,
            "include-hurdlecosts": bool,
            "include-tc-minstablepower": bool,
            "include-tc-min-ud-time": bool,
            "include-dayahead": bool,
            "include-strategicreserve": bool,
            "include-spinningreserve": bool,
            "include-primaryreserve": bool,
            "include-exportmps": bool,
        },
        "other preferences": {
            "power-fluctuations": str,
            "shedding-strategy": str,
            "shedding-policy": str,
            "unit-commitment-mode": str,
            "number-of-cores-mode": str,
            "day-ahead-reserve-management": str,
        },
        "advanced parameters": {
            "accuracy-on-correlation": str,
            "adequacy-block-size": int,
        },
        "seeds - Mersenne Twister": {
            "seed-tsgen-wind": int,
            "seed-tsgen-load": int,
            "seed-tsgen-hydro": int,
            "seed-tsgen-thermal": int,
            "seed-tsgen-solar": int,
            "seed-tsnumbers": int,
            "seed-unsupplied-energy-costs": int,
            "seed-spilled-energy-costs": int,
            "seed-thermal-costs": int,
            "seed-hydro-costs": int,
            "seed-initial-reservoir-levels": int,
        },
    }

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = deepcopy(GeneralData.TYPES)
        if config.version >= 650:
            types["other preferences"]["initial-reservoir-levels"] = str
        if config.version >= 700:
            types["optimization"]["link-type"] = str
        if config.version >= 710:
            types["general"]["thematic-trimming"] = bool
            types["general"]["geographic-trimming"] = bool
            del types["general"]["filtering"]
        if config.version >= 720:
            types["other preferences"]["hydro-pricing-mode"] = str
        if config.version >= 800:
            types["other preferences"]["hydro-heuristic-policy"] = str
            types["optimization"]["include-exportstructure"] = bool
            types["optimization"]["include-unfeasible-problem-behavior"] = str
            types["general"]["custom-scenario"] = bool
            del types["general"]["custom-ts-numbers"]
        if config.version >= 810:
            types["other preferences"]["renewable-generation-modelling"] = str
        if config.version >= 830:
            types["adequacy patch"] = {
                "include-adq-patch": bool,
                "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step": bool,
                "set-to-null-ntc-between-physical-out-for-first-step": bool,
            }
            types["optimization"]["include-split-exported-mps"] = bool
            types["optimization"][
                "include-exportmps"
            ] = str  # none, optim-1, optim-2, both-optims
        if config.version >= 840:
            del types["optimization"]["include-split-exported-mps"]
        if config.version >= 850:
            types["adequacy patch"]["price-taking-order"] = str
            types["adequacy patch"]["include-hurdle-cost-csr"] = bool
            types["adequacy patch"]["check-csr-cost-function"] = bool
            types["adequacy patch"][
                "threshold-initiate-curtailment-sharing-rule"
            ] = float
            types["adequacy patch"][
                "threshold-display-local-matching-rule-violations"
            ] = float
            types["adequacy patch"][
                "threshold-csr-variable-bounds-relaxation"
            ] = int

        IniFileNode.__init__(
            self,
            context,
            config,
            types=types,
            reader=MultipleSameKeysIniReader(DUPLICATE_KEYS),
            writer=IniWriter(special_keys=DUPLICATE_KEYS),
        )
