from enum import Enum
from typing import Any, Dict, Type

from pydantic import Field

from antarest.study.business.utils import FormFieldsBaseModel


class STStorageGroup(str, Enum):
    """
    This class defines the specific energy storage systems.

    Enum values:
        PSP_OPEN: Represents an open pumped storage plant.
        PSP_CLOSED: Represents a closed pumped storage plant.
        PONDAGE: Represents a pondage storage system (reservoir storage system).
        BATTERY: Represents a battery storage system.
        OTHER: Represents other energy storage systems.
    """

    PSP_OPEN = "PSP_open"
    PSP_CLOSED = "PSP_closed"
    PONDAGE = "Pondage"
    BATTERY = "Battery"
    OTHER = "Other"


# noinspection SpellCheckingInspection
class STStorageForm(FormFieldsBaseModel):
    """
    This class represents a form for short-term storage configuration.
    """

    class Config:
        allow_population_by_field_name = True

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["STStorageForm"]
        ) -> None:
            name: str
            for name, prop in schema.get("properties", {}).items():
                prop["title"] = name.replace("_", " ").title().replace(" ", "")
                prop["ini_alias"] = name.replace("_", "")

    name: str = Field(
        ...,
        description="Short-term storage name (mandatory)",
        regex=r"\w+",
    )
    group: STStorageGroup = Field(
        ...,
        description="Energy storage system group (mandatory)",
    )
    injection_nominal_capacity: float = Field(
        0,
        description="Injection nominal capacity (MW)",
        ge=0,
    )
    withdrawal_nominal_capacity: float = Field(
        0,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
    )
    reservoir_capacity: float = Field(
        0,
        description="Reservoir capacity (MWh)",
        ge=0,
    )
    efficiency: float = Field(
        1,
        description="Efficiency of the storage system",
        ge=0,
        le=1,
    )
    initial_level: float = Field(
        0,
        description="Initial level of the storage system",
        ge=0,
        le=1,
    )
    initial_level_optim: bool = Field(
        True,
        description="Flag indicating if the initial level is optimized",
    )


def _demo_st_storage():
    st_storage = STStorageForm(
        name="montezic",
        group=STStorageGroup.PSP_OPEN,
        injection_nominal_capacity=870.0,
        withdrawal_nominal_capacity=900.0,
        reservoir_capacity=31200.0,
        efficiency=0.75,
        initial_level_optim=True,
    )
    print(st_storage.json(by_alias=True))


if __name__ == "__main__":
    _demo_st_storage()
