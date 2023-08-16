import functools
import json
import operator
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

import numpy as np
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
from pydantic import BaseModel, Extra, Field, root_validator, validator
from typing_extensions import Literal


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

    class Config:
        @staticmethod
        def schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = STStorageCreateForm(
                name="Siemens Battery",
                group=STStorageGroup.BATTERY,
            )

    @property
    def to_config(self) -> STStorageConfig:
        values = self.dict(by_alias=False)
        return STStorageConfig(**values)


class STStorageInputForm(FormFieldsBaseModel):
    """
    Form used to **Edit** a short-term storage
    """

    name: Optional[str] = Field(
        None,
        description="Short-term storage name",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )
    group: Optional[STStorageGroup] = Field(
        description="Energy storage system group (mandatory)",
    )
    injection_nominal_capacity: Optional[float] = Field(
        None,
        description="Injection nominal capacity (MW)",
        ge=0,
    )
    withdrawal_nominal_capacity: Optional[float] = Field(
        None,
        description="Withdrawal nominal capacity (MW)",
        ge=0,
    )
    reservoir_capacity: Optional[float] = Field(
        None,
        description="Reservoir capacity (MWh)",
        ge=0,
    )
    efficiency: Optional[float] = Field(
        None,
        description="Efficiency of the storage system",
        ge=0,
        le=1,
    )
    initial_level: Optional[float] = Field(
        None,
        description="Initial level of the storage system",
        ge=0,
    )
    initial_level_optim: Optional[bool] = Field(
        None,
        description="Flag indicating if the initial level is optimized",
    )

    class Config:
        @staticmethod
        def schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = STStorageInputForm(
                name="Siemens Battery",
                group="Battery",
                injection_nominal_capacity=150,
                withdrawal_nominal_capacity=150,
                reservoir_capacity=600,
                efficiency=0.94,
                # initial_level is missing in this example ;-)
                initial_level_optim=True,
            )


class STStorageOutputForm(STStorageInputForm):
    """
    Form used to **Edit** a short-term storage
    """

    id: str = Field(
        description="Short-term storage ID",
        regex=r"[a-zA-Z0-9_(),& -]+",
    )
    group: STStorageGroup = Field(
        description="Energy storage system group (mandatory)",
    )

    class Config:
        @staticmethod
        def schema_extra(schema: MutableMapping[str, Any]) -> None:
            schema["example"] = STStorageOutputForm(
                id="siemens_battery",
                name="Siemens Battery",
                group=STStorageGroup.BATTERY,
                injection_nominal_capacity=150,
                withdrawal_nominal_capacity=150,
                reservoir_capacity=600,
                efficiency=0.94,
                initial_level_optim=True,
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


class STStorageMatrix(BaseModel):
    """
    Short-Term Storage Matrix  Model.

    This model represents a matrix associated with short-term storage
    and validates its integrity against specific conditions.

    Attributes:
        data: The 2D-array matrix containing time series values.
        index: List of lines for the data matrix.
        columns: List of columns for the data matrix.
    """

    class Config:
        extra = Extra.forbid

    data: List[List[float]]
    index: List[int]
    columns: List[int]

    @validator("data")
    def validate_time_series(
        cls, data: List[List[float]]
    ) -> List[List[float]]:
        """
        Validator to check the integrity of the time series data.

        Note:
            - The time series must have a shape of (8760, 1).
            - Time series values must not be empty or contain NaN values.
        """
        array = np.array(data)
        if array.size == 0:
            raise ValueError("time series must not be empty")
        if array.shape != (8760, 1):
            raise ValueError("time series must have shape (8760, 1)")
        if np.any(np.isnan(array)):
            raise ValueError("time series must not contain NaN values")
        return data


# noinspection SpellCheckingInspection
class STStorageMatrices(BaseModel):
    """
    Short-Term Storage Matrices Validation Model.

    This model is designed to validate constraints on short-term storage matrices.

    Attributes:
        pmax_injection: Matrix representing maximum injection values.
        pmax_withdrawal: Matrix representing maximum withdrawal values.
        lower_rule_curve: Matrix representing lower rule curve values.
        upper_rule_curve: Matrix representing upper rule curve values.
        inflows: Matrix representing inflow values.
    """

    class Config:
        extra = Extra.forbid

    pmax_injection: STStorageMatrix
    pmax_withdrawal: STStorageMatrix
    lower_rule_curve: STStorageMatrix
    upper_rule_curve: STStorageMatrix
    inflows: STStorageMatrix

    @validator(
        "pmax_injection",
        "pmax_withdrawal",
        "lower_rule_curve",
        "upper_rule_curve",
    )
    def validate_time_series(cls, matrix: STStorageMatrix) -> STStorageMatrix:
        """
        Validator to check if matrix values are within the range [0, 1].
        """
        array = np.array(matrix.data)
        if np.any(array < 0) or np.any(array > 1):
            raise ValueError("Matrix values should be between 0 and 1")
        return matrix

    @root_validator()
    def check_rule_curve(
        cls, values: MutableMapping[str, STStorageMatrix]
    ) -> MutableMapping[str, STStorageMatrix]:
        """
        Validator to ensure 'lower_rule_curve' values are less than
        or equal to 'upper_rule_curve' values.
        """
        if "lower_rule_curve" in values and "upper_rule_curve" in values:
            lower_rule_curve = values["lower_rule_curve"]
            upper_rule_curve = values["upper_rule_curve"]
            lower_array = np.array(lower_rule_curve.data, dtype=np.float64)
            upper_array = np.array(upper_rule_curve.data, dtype=np.float64)
            # noinspection PyUnresolvedReferences
            if (lower_array > upper_array).any():
                raise ValueError(
                    "Each 'lower_rule_curve' value must be lower"
                    " or equal to each 'upper_rule_curve'"
                )
        return values


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
            raise STStorageFieldsNotFoundError(storage_id
            ) from None
        return STStorageOutputForm.from_config(storage_id, config)

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
            raise STStorageFieldsNotFoundError(storage_id) from None
        else:
            old_config = STStorageConfig(**values)

        # use Python values to synchronize Config and Form values
        old_values = old_config.dict(exclude={"id"})
        new_values = form.dict(by_alias=False, exclude_none=True)
        updated = {**old_values, **new_values}
        new_config = STStorageConfig(**updated, id=storage_id)
        new_data = json.loads(new_config.json(by_alias=True, exclude={"id"}))

        # create the dict containing the old values (excluding defaults),
        # the updated values (including defaults)
        data: Dict[str, Any] = {}
        for field_name, field in new_config.__fields__.items():
            if field_name in {"id"}:
                continue
            value = getattr(new_config, field_name)
            if field_name in new_values or value != field.get_default():
                # use the JSON-converted value
                data[field.alias] = new_data[field.alias]

        # create the update config command with the modified data
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
        matrix = self._get_matrix_obj(study, area_id, storage_id, ts_name)
        return STStorageMatrix(**matrix)

    def _get_matrix_obj(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
    ) -> MutableMapping[str, Any]:
        # fmt: off
        file_study = self.storage_service.get_storage(study).get_raw(study)
        path = _SERIES_PATH.format(area_id=area_id, storage_id=storage_id, ts_name=ts_name)
        try:
            matrix = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageMatrixNotFoundError(
                study.id, area_id, storage_id, ts_name
            ) from None
        return matrix
        # fmt: on

    def update_matrix(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
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
        matrix_object = ts.dict()
        self._save_matrix_obj(
            study, area_id, storage_id, ts_name, matrix_object
        )

    def _save_matrix_obj(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
        matrix_obj: Dict[str, Any],
    ) -> None:
        # fmt: off
        file_study = self.storage_service.get_storage(study).get_raw(study)
        path = _SERIES_PATH.format(area_id=area_id, storage_id=storage_id, ts_name=ts_name)
        try:
            file_study.tree.save(matrix_obj, path.split("/"))
        except KeyError:
            raise STStorageMatrixNotFoundError(
                study.id, area_id, storage_id, ts_name
            ) from None
        # fmt: on

    def validate_matrices(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
    ) -> bool:
        """
        Validate the short-term storage matrices.

        This function validates the integrity of various matrices
        associated with a short-term storage in a given study and area.

        Note:
            - All matrices except "inflows" should have values between 0 and 1 (inclusive).
            - The values in the "lower_rule_curve" matrix should be less than or equal to
              the corresponding values in the "upper_rule_curve" matrix.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage to validate.

        Raises:
            ValidationError: If any of the matrices is invalid.

        Returns:
            bool: True if validation is successful.
        """
        # Create a partial function to retrieve matrix objects
        get_matrix_obj = functools.partial(
            self._get_matrix_obj, study, area_id, storage_id
        )

        # Validate matrices by constructing the `STStorageMatrices` object
        # noinspection SpellCheckingInspection
        STStorageMatrices(
            pmax_injection=get_matrix_obj("pmax_injection"),
            pmax_withdrawal=get_matrix_obj("pmax_withdrawal"),
            lower_rule_curve=get_matrix_obj("lower_rule_curve"),
            upper_rule_curve=get_matrix_obj("upper_rule_curve"),
            inflows=get_matrix_obj("inflows"),
        )

        # Validation successful
        return True
