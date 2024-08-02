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
        return CommandOutput(status=True, message=""), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        # todo: all the logic is here
        raise NotImplementedError()

    def to_dto(self) -> CommandDTO:
        return CommandDTO(action=self.command_name.value, args={})

    def match_signature(self) -> str:
        # This command has no attribute, therefore we can't differentiate 2 of these commands on the same study.
        return str(self.command_name.value)

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        # Same here
        raise NotImplementedError()

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        # Only used inside the cli app that no one uses I believe.
        raise NotImplementedError()

    def get_inner_matrices(self) -> t.List[str]:
        # This is used to get used matrices and not remove them inside the garbage collector loop.
        # todo: We should run the algo without the generation to know which clusters are concerned and then get the associated matrices
        raise NotImplementedError()
