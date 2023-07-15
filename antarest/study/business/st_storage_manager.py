import itertools
import json
import operator
import statistics
from typing import Any, Dict, List

import numpy as np
from antarest.study.business.areas.table_group import TableGroup
from antarest.study.business.utils import (
    Field,
    FormFieldsBaseModel as UtilsFormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    STStorageGroup,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_st_storage import (
    CreateSTStorage,
)
from antarest.study.storage.variantstudy.model.command.remove_st_storage import (
    RemoveSTStorage,
)
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)
from pydantic import BaseModel, Extra, validator


class FormFieldsBaseModel(UtilsFormFieldsBaseModel):
    """
    Pydantic Model for TableGroup
    """

    class Config:
        # alias_generator = to_camel_case
        # extra = Extra.forbid
        validate_assignment = True
        allow_population_by_field_name = True


class STStorageCreateForm(FormFieldsBaseModel):
    """
    Form used to **Create** a new short-term storage
    """

    name: str = Field(
        description="Short-term storage name",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )
    group: STStorageGroup = Field(
        description="Energy storage system group (mandatory)",
    )

    @property
    def to_config(self) -> STStorageConfig:
        values = self.dict(by_alias=False, exclude_none=True)
        return STStorageConfig(**values)


class STStorageEditForm(STStorageCreateForm):
    """
    Form used to **Edit** a short-term storage
    """

    id: str = Field(
        description="Short-term storage ID",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )
    # name: inherited
    # group: inherited
    injection_nominal_capacity: float = Field(
        None,
        description="Injection nominal capacity (MW)",
        ge=0,
    )
    withdrawal_nominal_capacity: float = Field(
        None,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
    )
    reservoir_capacity: float = Field(
        None,
        description="Reservoir capacity (MWh)",
        ge=0,
    )
    efficiency: float = Field(
        None,
        description="Efficiency of the storage system",
        ge=0,
        le=1,
    )
    initial_level: float = Field(
        None,
        description="Initial level of the storage system",
        ge=0,
    )
    initial_level_optim: bool = Field(
        None,
        description="Flag indicating if the initial level is optimized",
    )

    @classmethod
    def from_config(cls, storage_id: str, config: Dict[str, Any]) -> "STStorageEditForm":
        st_storage_config = STStorageConfig(id=storage_id, **config)
        values = st_storage_config.dict(by_alias=False, exclude_defaults=False)
        return cls(**values)


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

# Note: in the directory tree, there are directories called "clusters",
# but in reality they are short term storage.
ST_STORAGE_PATH = "input/thermal/clusters/{area_id}/list/{storage_id}"


class STStorageManagerError(Exception):
    """Base class of STStorageManager"""

    def __init__(self, study_id: str, area_id: str, reason: str) -> None:
        msg = (
            f"Error in the study '{study_id}',"
            f" the 'short-term storage' configuration of area '{area_id}' is invalid:"
            f" {reason}."
        )
        super().__init__(msg)


class STStorageFieldsNotFoundError(STStorageManagerError):
    """Fields of the short-term storage are not found"""

    def __init__(self, study_id: str, area_id: str, storage_id: str) -> None:
        super().__init__(
            study_id, area_id, f"Fields of storage '{storage_id}' not found"
        )


class STStorageConfigNotFoundError(STStorageManagerError):
    """Configuration for short-term storage is not found"""

    def __init__(self, study_id: str, area_id: str) -> None:
        super().__init__(study_id, area_id, "missing configuration")


class STStorageManager:
    """
    Manage short-term storage configuration in a study
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def create_st_storage(
        self,
        study: Study,
        area_id: str,
        form: STStorageCreateForm,
    ) -> str:
        """
        Create a new short-term storage configuration for the given `study`, `area_id`, and `storage_name`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            form: Form used to Create a new short-term storage.

        Returns:
            The ID of the newly created short-term storage.
        """
        st_storage_config = form.to_config
        command = CreateSTStorage(
            area_id=area_id,
            parameters=st_storage_config,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        # todo: La commande `execute_or_add_commands` devrait retourner un JSON.
        #  Ici, le JSON serait simplement l'ID du stockage court terme créé.
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )
        return st_storage_config.id

    def get_st_storge_groups(
        self,
        study: Study,
        area_id: str,
    ) -> TableGroup:
        """
        List of short-term storages grouped by types

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.

        Returns:
            The table or a group of tables for short-term storage groups.
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        try:
            config = file_study.tree.get(ST_STORAGE_PATH.split("/"), depth=3)
        except KeyError:
            raise STStorageConfigNotFoundError(study.id, area_id) from None
        else:
            # sourcery skip: extract-method
            # The Production Network contains all Production Groups.
            prod_network = TableGroup(
                properties={"name": f"Short-Term Storage of Area {area_id}"},
                operations={
                    "injectionNominalCapacity": sum,
                    "withdrawalNominalCapacity": sum,
                    "reservoirCapacity": sum,
                },
            )

            all_configs = [
                STStorageConfig(id=storage_id, **options)
                for storage_id, options in config.items()
            ]

            # Sort STStorageConfig by groups.
            order_by = operator.attrgetter("group")
            all_configs.sort(key=order_by)

            # Group STStorageConfig by groups.
            for group, configs in itertools.groupby(all_configs, key=order_by):
                group_name: str = group.value

                # Prepare the Production Units of that group.
                cfg: STStorageConfig
                elements = {
                    cfg.id: TableGroup(
                        properties={
                            "group": group_name,
                            "name": cfg.name,
                            "injectionNominalCapacity": cfg.injection_nominal_capacity,
                            "withdrawalNominalCapacity": cfg.withdrawal_nominal_capacity,
                            "reservoirCapacity": cfg.reservoir_capacity,
                            "efficiency": cfg.efficiency,
                        }
                    )
                    for cfg in configs
                }

                # The Production Group contains all Production Units of that group.
                prod_group = TableGroup(
                    properties={"name": group_name},
                    operations={
                        "injectionNominalCapacity": sum,
                        "withdrawalNominalCapacity": sum,
                        "reservoirCapacity": sum,
                        "efficiency": statistics.mean,
                    },
                    elements=elements,
                )

                prod_network.elements[group_name] = prod_group

            prod_network.calc_operations()
            return prod_network

    def get_st_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
    ) -> STStorageEditForm:
        """
        Get short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.

        Returns:
            Form used to Update a short-term storage.
        """
        # fmt: off
        file_study = self.storage_service.get_storage(study).get_raw(study)
        try:
            config = file_study.tree.get(
                ST_STORAGE_PATH.format(area_id=area_id, storage_id=storage_id).split("/"),
                depth=1,
            )
        except KeyError:
            raise STStorageFieldsNotFoundError(study.id, area_id, storage_id) from None
        else:
            return STStorageEditForm.from_config(storage_id, config)
        # fmt: on

    def update_st_storage(
        self,
        study: Study,
        area_id: str,
        form: STStorageEditForm,
    ) -> STStorageEditForm:
        """
        Set short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            form: Form used to Update a short-term storage.
        """
        # todo: Il faudrait une implémentation plus simple qui repose sur
        #  une nouvelle commande "update_st_storage" similaire à "create_st_storage".
        file_study = self.storage_service.get_storage(study).get_raw(study)
        try:
            # fmt: off
            values = file_study.tree.get(
                ST_STORAGE_PATH.format(area_id=area_id, storage_id=form.id).split("/"),
                depth=1,
            )
            # fmt: on
        except KeyError:
            raise STStorageFieldsNotFoundError(
                study.id, area_id, form.id
            ) from None
        else:
            old_config = STStorageConfig(id=form.id, **values)

        # use snake_case values
        old_values = old_config.dict(by_alias=False, exclude_defaults=False)
        new_values = form.dict(by_alias=False, exclude_none=True)
        updated = {**old_values, **new_values}
        new_config = STStorageConfig(**updated)
        data = json.loads(new_config.json(by_alias=True, exclude={"id"}))
        command = UpdateConfig(
            target=ST_STORAGE_PATH.format(area_id=area_id, storage=form.id),
            data=data,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

        values = new_config.dict(by_alias=False, exclude_defaults=False)
        return STStorageEditForm(**values)

    def delete_st_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
    ) -> None:
        """
        Delete a short-term storage configuration form the given study and area_id.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage to remove.
        """
        command = RemoveSTStorage(
            area_id=area_id,
            storage_id=storage_id,
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
        storage_id: str,
        ts_name: str,
    ) -> STStorageTimeSeries:
        """
        Get the time series `ts_name` for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            ts_name: Name of the time series to get.

        Returns:
            STStorageTimeSeries object containing the short-term storage configuration.
        """
        return STStorageTimeSeries()

    def update_time_series(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: str,
        ts: STStorageTimeSeries,
    ) -> None:
        """
        Update the time series `ts_name` for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            ts_name: Name of the time series to update.
            ts: Matrix of the time series to update.
        """
