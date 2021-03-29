from enum import Enum


class RoleType(Enum):
    ADMIN = "admin"
    RUNNER = "runner"
    WRITER = "writer"
    READER = "reader"
