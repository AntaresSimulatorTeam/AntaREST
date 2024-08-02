import typing as t

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.model import CommandDTO


class GenerateThermalClusterTimeSeries(ICommand):
    """
    Command used to generate thermal cluster timeseries for an entire study
    """

    command_name = CommandName.GENERATE_THERMAL_CLUSTER_TIMESERIES
    version = 1

    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        raise NotImplementedError()

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        raise NotImplementedError()

    def to_dto(self) -> CommandDTO:
        raise NotImplementedError()

    def match_signature(self) -> str:
        raise NotImplementedError()

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        raise NotImplementedError()

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        raise NotImplementedError()

    def get_inner_matrices(self) -> t.List[str]:
        raise NotImplementedError()
