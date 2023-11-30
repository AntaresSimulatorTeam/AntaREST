import typing as t

from pydantic import Field

from antarest.study.business.enum_ignore_case import EnumIgnoreCase
from antarest.study.storage.rawstudy.model.filesystem.config.cluster import ItemProperties
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import LowerCaseIdentifier

__all__ = (
    "STStorageGroup",
    "STStorageProperties",
    "STStorageConfig",
    "STStorageConfigType",
    "create_st_storage_config",
)


class STStorageGroup(EnumIgnoreCase):
    """
    This class defines the specific energy storage systems.

    Enum values:

        - PSP_OPEN: Represents an open pumped storage plant.
        - PSP_CLOSED: Represents a closed pumped storage plant.
        - PONDAGE: Represents a pondage storage system (reservoir storage system).
        - BATTERY: Represents a battery storage system.
        - OTHER1...OTHER5: Represents other energy storage systems.
    """

    PSP_OPEN = "PSP_open"
    PSP_CLOSED = "PSP_closed"
    PONDAGE = "Pondage"
    BATTERY = "Battery"
    OTHER1 = "Other1"
    OTHER2 = "Other2"
    OTHER3 = "Other3"
    OTHER4 = "Other4"
    OTHER5 = "Other5"


# noinspection SpellCheckingInspection
class STStorageProperties(ItemProperties):
    """
    Properties of a short-term storage system read from the configuration files.

    All aliases match the name of the corresponding field in the INI files.
    """

    group: STStorageGroup = Field(
        STStorageGroup.OTHER1,
        description="Energy storage system group",
    )
    injection_nominal_capacity: float = Field(
        0,
        description="Injection nominal capacity (MW)",
        ge=0,
        alias="injectionnominalcapacity",
    )
    withdrawal_nominal_capacity: float = Field(
        0,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
        alias="withdrawalnominalcapacity",
    )
    reservoir_capacity: float = Field(
        0,
        description="Reservoir capacity (MWh)",
        ge=0,
        alias="reservoircapacity",
    )
    efficiency: float = Field(
        1,
        description="Efficiency of the storage system (%)",
        ge=0,
        le=1,
    )
    # The `initial_level` value must be between 0 and 1, but the default value is 0.
    initial_level: float = Field(
        0.5,
        description="Initial level of the storage system (%)",
        ge=0,
        le=1,
        alias="initiallevel",
    )
    initial_level_optim: bool = Field(
        False,
        description="Flag indicating if the initial level is optimized",
        alias="initialleveloptim",
    )


# noinspection SpellCheckingInspection
class STStorageConfig(STStorageProperties, LowerCaseIdentifier):
    """
    Manage the configuration files in the context of Short-Term Storage.
    It provides a convenient way to read and write configuration data from/to an INI file format.

    Usage:

    >>> from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import STStorageConfig

    >>> st = STStorageConfig(name="Storage 1", group="battery", injection_nominal_capacity=1500)
    >>> st.id
    'storage 1'
    >>> st.group == STStorageGroup.BATTERY
    True
    >>> st.injection_nominal_capacity
    1500.0
    >>> st.injection_nominal_capacity = -897.32
    Traceback (most recent call last):
      ...
    pydantic.error_wrappers.ValidationError: 1 validation error for STStorageConfig
    injection_nominal_capacity
      ensure this value is greater than or equal to 0 (type=value_error.number.not_ge; limit_value=0)
    """


STStorageConfigType = STStorageConfig


def create_st_storage_config(study_version: t.Union[str, int], **kwargs: t.Any) -> STStorageConfigType:
    """
    Factory method to create a short-term storage configuration model.

    Args:
        study_version: The version of the study.
        **kwargs: The properties to be used to initialize the model.

    Returns:
        The short-term storage configuration model.

    Raises:
        ValueError: If the study version is not supported.
    """
    version = int(study_version)
    if version < 860:
        raise ValueError(f"Unsupported study version: {version}")
    return STStorageConfig(**kwargs)
