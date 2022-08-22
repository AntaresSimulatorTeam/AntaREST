from dataclasses import dataclass
from enum import Enum


@dataclass
class CommandOutput:
    status: bool
    message: str = ""


class TimeStep(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(Enum):
    BOTH = "both"
    EQUAL = "equal"
    GREATER = "greater"
    LESS = "less"


class CoeffType(Enum):
    THERMAL = "thermal"
    LINK = "link"


class CommandName(Enum):
    CREATE_AREA = "create_area"
    REMOVE_AREA = "remove_area"
    CREATE_DISTRICT = "create_district"
    REMOVE_DISTRICT = "remove_district"
    CREATE_LINK = "create_link"
    REMOVE_LINK = "remove_link"
    CREATE_BINDING_CONSTRAINT = "create_binding_constraint"
    UPDATE_BINDING_CONSTRAINT = "update_binding_constraint"
    REMOVE_BINDING_CONSTRAINT = "remove_binding_constraint"
    CREATE_CLUSTER = "create_cluster"
    REMOVE_CLUSTER = "remove_cluster"
    CREATE_RENEWABLES_CLUSTER = "create_renewables_cluster"
    REMOVE_RENEWABLES_CLUSTER = "remove_renewables_cluster"
    REPLACE_MATRIX = "replace_matrix"
    UPDATE_CONFIG = "update_config"
    UPDATE_COMMENTS = "update_comments"
    UPDATE_FILE = "update_file"
    UPDATE_DISTRICT = "update_district"
