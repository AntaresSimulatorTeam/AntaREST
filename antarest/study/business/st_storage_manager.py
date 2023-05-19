from enum import Enum
from typing import Any, Dict, List, Type

import numpy as np
from antarest.study.business.utils import (
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from pydantic import BaseModel, Extra, Field, validator

# =============
#  Form fields
# =============


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
class STStorageFields(FormFieldsBaseModel):
    """
    This class represents a form for short-term storage configuration.
    """

    class Config:
        allow_population_by_field_name = True

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["STStorageFields"]
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


# =============
#  Time series
# =============


MATRIX_SHAPE = (8670, 1)


class STStorageTimeSeries(BaseModel):
    class Config:
        extra = Extra.forbid

    data: List[List[float]]
    index: List[int]
    columns: List[int]

    @validator("data")
    def validate_time_series(
        cls, data: List[List[float]]
    ) -> List[List[float]]:
        """Validate the time series."""
        array = np.array(data)
        if array.size == 0:
            raise ValueError("time series must not be empty")
        if array.shape != MATRIX_SHAPE:
            raise ValueError(f"time series must have shape {MATRIX_SHAPE}")
        if np.any(np.isnan(array)):
            raise ValueError("time series must not contain NaN values")
        return data


# ============================
#  Short-term storage manager
# ============================

ST_STORAGE_PATH = "input/thermal/clusters/{area}/list/{cluster}"


class STStorageFieldsNotFoundError(Exception):
    """Fields of the short-term storage cluster are not found"""


class STStorageManager:
    """
    Manage short-term storage clusters configuration in a study
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def create_st_storage(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        field_values: STStorageFields,
    ) -> None:
        """
        Create a new short-term storage cluster configuration for the given `study`, `area_id`, and `cluster_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster.
            field_values: STStorageFields object containing the short-term storage cluster configuration.
        """
        # NOTE: The form field names are in camelCase,
        # while the configuration field names are in snake_case.
        thermal_config = field_values.to_ini()
        command = CreateSTStorage(
            target=ST_STORAGE_PATH.format(area=area_id, cluster=cluster_id),
            data=thermal_config,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def list_st_storage(
        self,
        study: Study,
        area_id: str,
    ) -> STStorageFields:
        """
        List of short-term storages grouped by cluster types

        Args:
            study:
            area_id:

        Returns:
        """

    def get_st_storage(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
    ) -> STStorageFields:
        """
        Get short-term storage cluster configuration for the given `study`, `area_id`, and `cluster_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster.

        Returns:
            STStorageFields object containing the short-term storage cluster configuration.
        """

        file_study = self.storage_service.get_storage(study).get_raw(study)
        # fmt: off
        try:
            thermal_config = file_study.tree.get(
                ST_STORAGE_PATH.format(area=area_id, cluster=cluster_id).split("/"),
                depth=1,
            )
        except KeyError:
            raise STStorageFieldsNotFoundError(
                f"Fields of short-term storage cluster '{cluster_id}' not found in '{area_id}'"
            ) from None
        else:
            return STStorageFields.from_ini(thermal_config)
        # fmt: on

    def update_st_storage(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        field_values: STStorageFields,
    ) -> None:
        """
        Set short-term storage cluster configuration for the given `study`, `area_id`, and `cluster_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster.
            field_values: STStorageFields object containing the short-term storage cluster configuration.
        """
        # NOTE: The form field names are in camelCase,
        # while the configuration field names are in snake_case.
        thermal_config = field_values.to_ini()
        command = UpdateConfig(
            target=ST_STORAGE_PATH.format(area=area_id, cluster=cluster_id),
            data=thermal_config,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def delete_st_storage(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
    ) -> None:
        """
        Delete a short-term storage cluster configuration form the given study and area_id.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster to remove.
        """
        command = RemoveSTStorage(
            area_id=area_id,
            cluster_id=cluster_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    def get_time_series(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        ts_name: str,
    ) -> STStorageTimeSeries:
        """
        Get the time series `ts_name` for the given `study`, `area_id`, and `cluster_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster.
            ts_name: Name of the time series to get.

        Returns:
            STStorageTimeSeries object containing the short-term storage cluster configuration.
        """
        return STStorageTimeSeries()

    def update_time_series(
        self,
        study: Study,
        area_id: str,
        cluster_id: str,
        ts_name: str,
        ts: STStorageTimeSeries,
    ) -> None:
        """
        Update the time series `ts_name` for the given `study`, `area_id`, and `cluster_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage cluster.
            cluster_id: The cluster ID of the short-term storage cluster.
            ts_name: Name of the time series to update.
            ts: Matrix of the time series to update.
        """
