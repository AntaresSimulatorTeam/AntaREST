"""
Packaging exceptions
"""


class PackagingException(Exception):
    """Base class of all packaging exceptions"""


class DetectionError(PackagingException):
    def __init__(self, system: str) -> None:
        super().__init__(
            f"Running on a {system} distribution other than Windows, Ubuntu or CentOS"
        )
