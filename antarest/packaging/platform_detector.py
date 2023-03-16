"""
System Platform Detection
"""
import enum
import logging
import platform

from antarest.packaging.exceptions import DetectionError

logger=logging.getLogger(__name__)


class Platform(enum.Enum):
    WINDOWS = "Windows"
    UBUNTU = "Ubuntu"
    CENT_OS = "CentOS"

    @classmethod
    def auto_detect(cls) -> "Platform":
        logger.info("Auto-detecting local platform...")
        system = platform.system()
        if system == "Windows":
            return cls.WINDOWS
        elif system == "Linux":
            try:
                with open("/etc/os-release", mode="r") as f:
                    distro = f.readline().strip().split("=")[1].strip('"')
                if distro == "Ubuntu":
                    return cls.UBUNTU
                elif distro == "CentOS Linux":
                    return cls.CENT_OS
                else:
                    raise DetectionError(system)
            except FileNotFoundError:
                raise DetectionError(system) from None
        else:
            raise DetectionError(system)
