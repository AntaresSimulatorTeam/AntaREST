import logging
import shutil
from pathlib import Path
from typing import List, Optional, Callable

from antarest.core.utils.utils import StopWatch
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
        notifier: Optional[Callable[[int, bool, str], None]] = None,
    ) -> GenerationResultInfoDTO:
        stopwatch = StopWatch()

        # Build file study
        logger.info("Building study tree")
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

        stopwatch.reset_current()
        logger.info("Applying commands")
        command_index = 0
        total_commands = len(commands)
        study_id = metadata.id if metadata is not None else "-"
        for command in commands:
            command_output_status = False
            command_output_message = ""
            try:
                command_index += 1
                output = command.apply(file_study)
                command_output_status = output.status
                command_output_message = output.message
            except Exception as e:
                command_output_message = f"Error while applying command {command.command_name.value}"
                logger.error(command_output_message, exc_info=e)
                break
            finally:
                results.details.append(
                    (
                        command.command_name.value,
                        command_output_status,
                        command_output_message,
                    )
                )
                results.success = command_output_status
                if notifier:
                    notifier(
                        command_index - 1,
                        command_output_status,
                        command_output_message,
                    )
                stopwatch.log_elapsed(
                    lambda x: logger.info(
                        f"Command {command_index}/{total_commands} [{study_id}] {command.match_signature()} applied in {x}s"
                    )
                )

            if not results.success:
                break

        if not results.success and delete_on_failure:
            shutil.rmtree(dest_path)
        stopwatch.log_elapsed(
            lambda x: logger.info(f"Variant generation done in {x}s"),
            since_start=True,
        )
        return results
