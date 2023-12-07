from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode


# noinspection SpellCheckingInspection
class BindingConstraintsIni(IniFileNode):
    """
    Handle the binding constraints configuration file: `/input/bindingconstraints/bindingconstraints.ini`.

    This files contains a list of sections numbered from 1 to n.

    Each section contains the following fields:

    - `name`: the name of the binding constraint.
    - `id`: the id of the binding constraint (normalized name in lower case).
    - `enabled`: whether the binding constraint is enabled or not.
    - `type`: the frequency of the binding constraint ("hourly", "daily" or "weekly")
    - `operator`: the operator of the binding constraint ("both", "equal", "greater", "less")
    - `comment`: a comment
    - and a list of coefficients (one per line) of the form `{area1}%{area2} = {coeff}`.
    """

    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, types={})
