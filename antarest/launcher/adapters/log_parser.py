import logging
import re

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LaunchProgressDTO(BaseModel):
    progress: float = 0
    total_mc_years: int = 1

    def update_progress(self, line: str) -> bool:
        if "MC-Years : [" in line:
            if regex_result := re.search(
                r"MC-Years : \[\d+ .. \d+], total: (\d+)", line
            ):
                self.total_mc_years = int(regex_result[1])
                return True
            else:
                logger.warning(
                    f"Failed to extract log progress batch size on line : {line}"
                )
                return False
        elif "Exporting the annual results" in line:
            self.progress += 98 / self.total_mc_years
            return True
        elif "Exporting the survey results" in line:
            self.progress = 99
            return True
        elif "Quitting the solver gracefully" in line:
            self.progress = 100
            return True
        return False
