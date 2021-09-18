import logging
import shutil
from pathlib import Path
from typing import List, Optional

from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.utils import update_antares_info
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy
from antarest.study.storage.variantstudy.model.model import (
    GenerationResultInfoDTO,
)

logger = logging.getLogger(__name__)


class VariantCommandGenerator:
    def __init__(self, study_factory: StudyFactory) -> None:
        self.study_factory = study_factory

    def generate(
        self,
        commands: List[ICommand],
        dest_path: Path,
        metadata: Optional[VariantStudy] = None,
        delete_on_failure: bool = True,
    ) -> GenerationResultInfoDTO:

        # Build file study
        study_config, study_tree = self.study_factory.create_from_fs(
            dest_path, "", use_cache=False
        )
        if metadata:
            update_antares_info(metadata, study_tree)
        file_study = FileStudy(config=study_config, tree=study_tree)

        # Apply commands
        results: GenerationResultInfoDTO = GenerationResultInfoDTO(
            success=True, details=[]
        )

        for command in commands:
            try:
                output = command.apply(file_study)
            except Exception as e:
                results.success = False
                message = f"Error while applying command {command.command_name.value}"
                logger.error(message, exc_info=e)
                results.details.append(
                    (command.command_name.value, False, message)
                )
                break

            results.details.append(
                (command.command_name.value, output.status, output.message)
            )
            results.success = results.success and output.status

            if not output.status:
                break

        if not results.success and delete_on_failure:
            shutil.rmtree(dest_path)
        return results
