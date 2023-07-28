import logging
import re

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class LaunchProgressDTO(BaseModel):
    progress: float = 0
    total_mc_years_to_perform: int = 1


class LogParser:
    @staticmethod
    def update_progress(
        line: str, launch_progress_dto: LaunchProgressDTO
    ) -> bool:
        if "MC-Years : [" in line:
            if regex_result := re.search(
                r"MC-Years : \[\d+ .. \d+], total: (\d+)", line
            ):
                launch_progress_dto.total_mc_years_to_perform = int(
                    regex_result[1]
                )
                return True
            else:
                logger.warning(
                    f"Failed to extract log progress batch size on line : {line}"
                )
                return False
        elif "Exporting the annual results" in line:
            launch_progress_dto.progress += (
                98 / launch_progress_dto.total_mc_years_to_perform
            )
            return True
        elif "Exporting the survey results" in line:
            launch_progress_dto.progress = 99
            return True
        elif "Quitting the solver gracefully" in line:
            launch_progress_dto.progress = 100
            return True
        return False
