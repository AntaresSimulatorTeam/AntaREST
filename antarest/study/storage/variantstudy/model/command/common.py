from enum import Enum

from dataclasses import dataclass


@dataclass
class CommandOutput:
    status: bool
    message: str


class TimeStep(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class Operator(Enum):
    BOTH = "both"
    EQUAL = "equal"
    GREATER = "greater"
    LESS = "less"


class CoeffType(Enum):
    THERMAL = "thermal"
    LINK = "link"


class CommandName(Enum):
    CREATE_AREA = "create_area"
    UPDATE_AREA = "update_area"
    REMOVE_AREA = "remove_area"
    CREATE_DISTRICT = "create_district"
    UPDATE_DISTRICT = "update_district"
    REMOVE_DISTRICT = "remove_district"
    CREATE_LINK = "create_link"
    UPDATE_LINK = "update_link"
    REMOVE_LINK = "remove_link"
    CREATE_BINDING_CONSTRAINS = "create_binding_constrains"
    UPDATE_BINDING_CONSTRAINS = "update_binding_constrains"
    REMOVE_BINDING_CONSTRAINS = "remove_binding_constrains"
    CREATE_CLUSTER = "create_cluster"
    UPDATE_CLUSTER = "update_cluster"
    REMOVE_CLUSTER = "remove_cluster"
    REPLACE_MATRIX = "replace_matrix"
    UPDATE_CONFIG = "update_config"
