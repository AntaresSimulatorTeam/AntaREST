import logging
import shutil
from pathlib import Path
from typing import List, Optional, Callable, Tuple

from antarest.core.utils.utils import StopWatch
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
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
        commands: List[List[ICommand]],
        dest_path: Path,
        metadata: Optional[VariantStudy] = None,
        delete_on_failure: bool = True,
        notifier: Optional[Callable[[int, bool, str], None]] = None,
        light: bool = False,
    ) -> Tuple[GenerationResultInfoDTO, FileStudyTreeConfig]:
        stopwatch = StopWatch()

        # Build file study
        logger.info(
            "Building config (light generation)"
            if light
            else "Building study tree"
        )
        study_config, study_tree = self.study_factory.create_from_fs(
            dest_path, "", use_cache=False
        )
        if metadata and not light:
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
        for command_batch in commands:
            command_output_status = True
            command_output_message = ""
            command_name = (
                command_batch[0].command_name.value
                if len(command_batch) > 0
                else ""
            )
            try:
                command_index += 1
                command_output_messages: List[str] = []
                for command in command_batch:
                    output = (
                        command.apply_config(file_study)
                        if light
                        else command.apply(file_study)
                    )
                    command_output_messages.append(output.message)
                    command_output_status = (
                        command_output_status and output.status
                    )
                    if not command_output_status:
                        break
                command_output_message = "\n".join(command_output_messages)
            except Exception as e:
                command_output_status = False
                command_output_message = (
                    f"Error while applying command {command_name}"
                )
                logger.error(command_output_message, exc_info=e)
                break
            finally:
                results.details.append(
                    (
                        command_name,
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

        if not results.success and delete_on_failure and not light:
            shutil.rmtree(dest_path)
        stopwatch.log_elapsed(
            lambda x: logger.info(
                f"Variant{' light ' if light else ' '}generation done in {x}s"
            ),
            since_start=True,
        )
        return results, study_config
