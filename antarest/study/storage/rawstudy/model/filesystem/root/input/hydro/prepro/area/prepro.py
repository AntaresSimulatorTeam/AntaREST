from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


# noinspection SpellCheckingInspection
class InputHydroPreproAreaPrepro(IniFileNode):
    """
    Configuration for the hydraulic Inflow Structure:

    - intermonthly-correlation: Average correlation between the energy of a month and
      that of the next month (inter-monthly correlation).

    See: https://antares-simulator.readthedocs.io/en/latest/reference-guide/04-active_windows/#hydro
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        types = {"prepro": {"intermonthly-correlation": float}}
        IniFileNode.__init__(self, context, config, types)
