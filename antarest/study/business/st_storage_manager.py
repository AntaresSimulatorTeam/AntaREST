import json
import operator
from typing import Any, List, Mapping, Sequence

import numpy as np
from typing_extensions import Literal

from antarest.core.exceptions import (
    STStorageConfigNotFoundError,
    STStorageFieldsNotFoundError,
    STStorageMatrixNotFoundError,
)
from antarest.study.business.utils import (
    FormFieldsBaseModel as UtilsFormFieldsBaseModel,
)
from antarest.study.business.utils import execute_or_add_commands
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
from pydantic import BaseModel, Extra, Field, validator


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
        values = self.dict(by_alias=False)
        return STStorageConfig(**values)


class STStorageInputForm(STStorageCreateForm):
    """
    Form used to **Edit** a short-term storage
    """

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


class STStorageOutputForm(STStorageInputForm):
    """
    Form used to **Edit** a short-term storage
    """

    id: str = Field(
        description="Short-term storage ID",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )

    @classmethod
    def from_config(
        cls, storage_id: str, config: Mapping[str, Any]
    ) -> "STStorageOutputForm":
        st_storage_config = STStorageConfig(**config, id=storage_id)
        values = st_storage_config.dict(by_alias=False)
        return cls(**values)


# =============
#  Time series
# =============


MATRIX_SHAPE = (8760, 1)


class STStorageMatrix(BaseModel):
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


# noinspection SpellCheckingInspection
STStorageTimeSeries = Literal[
    "pmax_injection",
    "pmax_withdrawal",
    "lower_rule_curve",
    "upper_rule_curve",
    "inflows",
]

# ============================
#  Short-term storage manager
# ============================

# Note: in the directory tree, there are directories called "clusters",
# but in reality they are short term storage.
_LIST_PATH = "input/st-storage/clusters/{area_id}/list/{storage_id}"
_SERIES_PATH = "input/st-storage/series/{area_id}/{storage_id}/{ts_name}"


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
        # todo: The `execute_or_add_commands` command should return a JSON object.
        #  Here, the JSON object should simply be the created short term storage ID.
        execute_or_add_commands(
            study,
            file_study,
            [command],
            self.storage_service,
        )
        return st_storage_config.id

    def get_st_storages(
        self,
        study: Study,
        area_id: str,
    ) -> Sequence[STStorageOutputForm]:
        """
        Get the list of short-term storage configurations for the given `study`, and `area_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.

        Returns:
            The list of forms used to display the short-term storages.
        """
        # fmt: off
        file_study = self.storage_service.get_storage(study).get_raw(study)
        path = _LIST_PATH.format(area_id=area_id, storage_id="")[:-1]
        try:
            config = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise STStorageConfigNotFoundError(study.id, area_id) from None
        # fmt: on
        # Sort STStorageConfig by groups and then by name
        order_by = operator.attrgetter("group", "name")
        all_configs = sorted(
            (
                STStorageConfig(id=storage_id, **options)
                for storage_id, options in config.items()
            ),
            key=order_by,
        )
        return tuple(
            STStorageOutputForm(**config.dict(by_alias=False))
            for config in all_configs
        )

    def get_st_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
    ) -> STStorageOutputForm:
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
        path = _LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            config = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageFieldsNotFoundError(
                study.id, area_id, storage_id
            ) from None
        return STStorageOutputForm.from_config(storage_id, config)
        # fmt: on

    def update_st_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        form: STStorageInputForm,
    ) -> STStorageOutputForm:
        """
        Set short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            form: Form used to Update a short-term storage.
        """
        # todo: We should have a more simple implementation based on
        #  a new `update_st_storage` command similar to `create_st_storage`.
        file_study = self.storage_service.get_storage(study).get_raw(study)
        path = _LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            values = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageFieldsNotFoundError(
                study.id, area_id, storage_id
            ) from None
        else:
            old_config = STStorageConfig(**values)

        # use snake_case values
        old_values = old_config.dict(
            by_alias=False, exclude_defaults=False, exclude={"id"}
        )
        new_values = form.dict(by_alias=False)
        updated = {**old_values, **new_values}
        new_config = STStorageConfig(**updated, id=storage_id)
        data = json.loads(new_config.json(by_alias=True, exclude={"id"}))
        command = UpdateConfig(
            target=path,
            data=data,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

        values = new_config.dict(by_alias=False)
        return STStorageOutputForm(**values)

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

    def get_matrix(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
    ) -> STStorageMatrix:
        """
        Get the time series `ts_name` for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            ts_name: Name of the time series to get.

        Returns:
            STStorageMatrix object containing the short-term storage configuration.
        """
        # fmt: off
        file_study = self.storage_service.get_storage(study).get_raw(study)
        path = _SERIES_PATH.format(area_id=area_id, storage_id=storage_id, ts_name=ts_name)
        try:
            matrix = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageMatrixNotFoundError(study.id, area_id, storage_id, ts_name) from None
        return STStorageMatrix(**matrix)
        # fmt: on

    def update_matrix(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: str,
        ts: STStorageMatrix,
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
