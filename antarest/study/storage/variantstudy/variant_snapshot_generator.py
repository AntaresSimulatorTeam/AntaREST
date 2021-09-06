import shutil
from pathlib import Path
from typing import List

from antarest.study.model import RawStudy
from antarest.study.storage.rawstudy.exporter_service import ExporterService
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.utils import update_antares_info
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model import (
    GenerationResultInfoDTO,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import (
    VariantStudy,
)


class VariantSnapshotGenerator:
    """
    Service to generate a variant study by applying commands to original study
    """

    def __init__(
        self,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        exporter_service: ExporterService,
    ):
        self.command_factory = command_factory
        self.study_factory = study_factory
        self.exporter_service = exporter_service

    def generate_snapshot(
        self, variant_study: VariantStudy, parent_study: RawStudy
    ) -> GenerationResultInfoDTO:

        # Copy parent study to dest
        src_path = Path(parent_study.path)
        dest_path = Path(variant_study.path / "snapshot")

        self.exporter_service.export_flat(src_path, dest_path)

        # Build file study
        study_config, study_tree = self.study_factory.create_from_fs(
            dest_path, study_id=variant_study.id
        )
        update_antares_info(variant_study, study_tree)
        file_study = FileStudy(config=study_config, tree=study_tree)

        # Apply commands
        commands: List[ICommand] = []
        for command_block in variant_study.commands:
            commands.extend(
                self.command_factory.to_icommand(command_block.to_dto())
            )

        results: GenerationResultInfoDTO = GenerationResultInfoDTO(
            success=True, details=[]
        )
        for command in commands:
            output = command.apply(file_study)
            results.details.append(
                (command.command_name.value, output.status, output.message)
            )
            results.success = results.success and output.status
            if not output.status:
                break

        if not results.success:
            shutil.rmtree(dest_path)

        return results
