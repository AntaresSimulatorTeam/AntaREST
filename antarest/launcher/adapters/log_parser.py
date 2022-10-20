import logging
import re

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class LaunchProgressDTO(BaseModel):
    coef: float = 0.8
    progress: float = 0
    N_ANNUAL_RESULT: int = 1
    N_K: int = 1


class LogParser:
    @staticmethod
    def update_progress(
        line: str, launch_progress_dto: LaunchProgressDTO
    ) -> bool:
        if "MC-Years : [" in line:
            regex = re.compile(
                r".+?(?:\s\.\.\s)(\d+).+?(\d+)"
            )  # group 1 is the first number after " .. ", and group 2 is the las number of the line
            mo = regex.search(line)
            launch_progress_dto.N_K = int(mo.group(1))  # type:ignore
            launch_progress_dto.N_ANNUAL_RESULT = int(
                mo.group(2)  # type:ignore
            )
            return True
        elif "parallel batch size : " in line:
            mk = re.search(r"parallel batch size : (\d+)", line)
            if mk:
                K = int(mk.group(1))
                launch_progress_dto.progress += (
                    launch_progress_dto.coef * 90 * K / launch_progress_dto.N_K
                )
                return True
            else:
                logger.warning(
                    f"Failed to extract log progress batch size on line : {line}"
                )
        elif "Exporting the annual results" in line:
            launch_progress_dto.progress += (
                launch_progress_dto.coef
                * 9
                * 1
                / launch_progress_dto.N_ANNUAL_RESULT
            )
            return True
        elif "Exporting the survey results" in line:
            launch_progress_dto.progress = launch_progress_dto.coef * 99
            return True
        return False
