import functools
import json
import operator
import typing as t

import numpy as np
from pydantic import BaseModel, Extra, root_validator, validator
from typing_extensions import Literal

from antarest.core.exceptions import (
    ClusterAlreadyExists,
    STStorageConfigNotFoundError,
    STStorageFieldsNotFoundError,
    STStorageMatrixNotFoundError,
)
from antarest.study.business.utils import AllOptionalMetaclass, camel_case_model, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
    STStorageGroup,
    STStorageProperties,
    create_st_storage_config,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_st_storage import CreateSTStorage
from antarest.study.storage.variantstudy.model.command.remove_st_storage import RemoveSTStorage
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

__all__ = (
    "STStorageManager",
    "STStorageCreation",
    "STStorageInput",
    "STStorageOutput",
    "STStorageMatrix",
    "STStorageTimeSeries",
)


@camel_case_model
class STStorageInput(STStorageProperties, metaclass=AllOptionalMetaclass, use_none=True):
    """
    Model representing the form used to EDIT an existing short-term storage.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = STStorageInput(
                name="Siemens Battery",
                group=STStorageGroup.BATTERY,
                injection_nominal_capacity=150,
                withdrawal_nominal_capacity=150,
                reservoir_capacity=600,
                efficiency=0.94,
                initial_level=0.5,
                initial_level_optim=True,
            )


class STStorageCreation(STStorageInput):
    """
    Model representing the form used to CREATE a new short-term storage.
    """

    # noinspection Pydantic
    @validator("name", pre=True)
    def validate_name(cls, name: t.Optional[str]) -> str:
        """
        Validator to check if the name is not empty.
        """
        if not name:
            raise ValueError("'name' must not be empty")
        return name

    @property
    def to_config(self) -> STStorageConfig:
        values = self.dict(by_alias=False, exclude_none=True)
        return STStorageConfig(**values)


@camel_case_model
class STStorageOutput(STStorageConfig):
    """
    Model representing the form used to display the details of a short-term storage entry.
    """

    class Config:
        @staticmethod
        def schema_extra(schema: t.MutableMapping[str, t.Any]) -> None:
            schema["example"] = STStorageOutput(
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
    def from_config(cls, storage_id: str, config: t.Mapping[str, t.Any]) -> "STStorageOutput":
        storage = STStorageConfig(**config, id=storage_id)
        values = storage.dict(by_alias=False)
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

    data: t.List[t.List[float]]
    index: t.List[int]
    columns: t.List[int]

    @validator("data")
    def validate_time_series(cls, data: t.List[t.List[float]]) -> t.List[t.List[float]]:
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
            raise ValueError(f"time series must have shape ({8760}, 1)")
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
        if np.any((array < 0) | (array > 1)):
            raise ValueError("Matrix values should be between 0 and 1")
        return matrix

    @root_validator()
    def validate_rule_curve(
        cls, values: t.MutableMapping[str, STStorageMatrix]
    ) -> t.MutableMapping[str, STStorageMatrix]:
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
                raise ValueError("Each 'lower_rule_curve' value must be lower or equal to each 'upper_rule_curve'")
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


STORAGE_LIST_PATH = "input/st-storage/clusters/{area_id}/list/{storage_id}"
STORAGE_SERIES_PATH = "input/st-storage/series/{area_id}/{storage_id}/{ts_name}"


class STStorageManager:
    """
    Manage short-term storage configuration in a study
    """

    def __init__(self, storage_service: StudyStorageService):
        self.storage_service = storage_service

    def _get_file_study(self, study: Study) -> FileStudy:
        """
        Helper function to get raw study data.
        """

        return self.storage_service.get_storage(study).get_raw(study)

    def create_storage(
        self,
        study: Study,
        area_id: str,
        form: STStorageCreation,
    ) -> STStorageOutput:
        """
        Create a new short-term storage configuration for the given `study`, `area_id`, and `form fields`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            form: Form used to Create a new short-term storage.

        Returns:
            The ID of the newly created short-term storage.
        """
        storage = form.to_config
        command = CreateSTStorage(
            area_id=area_id,
            parameters=storage,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self._get_file_study(study)
        execute_or_add_commands(
            study,
            file_study,
            [command],
            self.storage_service,
        )

        return self.get_storage(study, area_id, storage_id=storage.id)

    def get_storages(
        self,
        study: Study,
        area_id: str,
    ) -> t.Sequence[STStorageOutput]:
        """
        Get the list of short-term storage configurations for the given `study`, and `area_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.

        Returns:
            The list of forms used to display the short-term storages.
        """

        file_study = self._get_file_study(study)
        path = STORAGE_LIST_PATH.format(area_id=area_id, storage_id="")[:-1]
        try:
            config = file_study.tree.get(path.split("/"), depth=3)
        except KeyError:
            raise STStorageConfigNotFoundError(study.id, area_id) from None

        # Sort STStorageConfig by groups and then by name
        order_by = operator.attrgetter("group", "name")
        all_configs = sorted(
            (STStorageConfig(id=storage_id, **options) for storage_id, options in config.items()),
            key=order_by,
        )
        return tuple(STStorageOutput(**config.dict(by_alias=False)) for config in all_configs)

    def get_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
    ) -> STStorageOutput:
        """
        Get short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.

        Returns:
            Form used to display and edit a short-term storage.
        """

        file_study = self._get_file_study(study)
        path = STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            config = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageFieldsNotFoundError(storage_id) from None
        return STStorageOutput.from_config(storage_id, config)

    def update_storage(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        form: STStorageInput,
    ) -> STStorageOutput:
        """
        Set short-term storage configuration for the given `study`, `area_id`, and `storage_id`.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_id: The ID of the short-term storage.
            form: Form used to Update a short-term storage.
        Returns:
            Updated form of short-term storage.
        """
        study_version = study.version

        # review: reading the configuration poses a problem for variants,
        #  because it requires generating a snapshot, which takes time.
        #  This reading could be avoided if we don't need the previous values
        #  (no cross-field validation, no default values, etc.).
        #  In return, we won't be able to return a complete `STStorageOutput` object.
        #  So, we need to make sure the frontend doesn't need the missing fields.
        #  This missing information could also be a problem for the API users.
        #  The solution would be to avoid reading the configuration if the study is a variant
        #  (we then use the default values), otherwise, for a RAW study, we read the configuration
        #  and update the modified values.

        file_study = self._get_file_study(study)

        path = STORAGE_LIST_PATH.format(area_id=area_id, storage_id=storage_id)
        try:
            values = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageFieldsNotFoundError(storage_id) from None
        else:
            old_config = create_st_storage_config(study_version, **values)

        # use Python values to synchronize Config and Form values
        new_values = form.dict(by_alias=False, exclude_none=True)
        new_config = old_config.copy(exclude={"id"}, update=new_values)
        new_data = json.loads(new_config.json(by_alias=True, exclude={"id"}))

        # create the dict containing the new values using aliases
        data: t.Dict[str, t.Any] = {
            field.alias: new_data[field.alias]
            for field_name, field in new_config.__fields__.items()
            if field_name in new_values
        }

        # create the update config commands with the modified data
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        commands = [
            UpdateConfig(target=f"{path}/{key}", data=value, command_context=command_context)
            for key, value in data.items()
        ]
        execute_or_add_commands(study, file_study, commands, self.storage_service)

        values = new_config.dict(by_alias=False)
        return STStorageOutput(**values, id=storage_id)

    def delete_storages(
        self,
        study: Study,
        area_id: str,
        storage_ids: t.Sequence[str],
    ) -> None:
        """
        Delete short-term storage configurations form the given study and area_id.

        Args:
            study: The study object.
            area_id: The area ID of the short-term storage.
            storage_ids: IDs list of short-term storages to remove.
        """
        command_context = self.storage_service.variant_study_service.command_factory.command_context
        for storage_id in storage_ids:
            command = RemoveSTStorage(
                area_id=area_id,
                storage_id=storage_id,
                command_context=command_context,
            )
            file_study = self._get_file_study(study)
            execute_or_add_commands(study, file_study, [command], self.storage_service)

    def duplicate_cluster(self, study: Study, area_id: str, source_id: str, new_name: str) -> STStorageOutput:
        """
        Creates a duplicate cluster within the study area with a new name.

        Args:
            study: The study in which the cluster will be duplicated.
            area_id: The identifier of the area where the cluster will be duplicated.
            source_id: The identifier of the cluster to be duplicated.
            new_name: The new name for the duplicated cluster.

        Returns:
            The duplicated cluster configuration.

        Raises:
            ClusterAlreadyExists: If a cluster with the new name already exists in the area.
        """
        new_id = transform_name_to_id(new_name)
        existing_ids = [storage.id for storage in self.get_storages(study, area_id)]
        if new_id in existing_ids:
            raise ClusterAlreadyExists("Short term storage", new_id)

        # Cluster duplication
        current_cluster = self.get_storage(study, area_id, source_id)
        current_cluster.name = new_name
        creation_form = STStorageCreation(**current_cluster.dict(by_alias=False, exclude={"id"}))
        new_storage = self.create_storage(study, area_id, creation_form)

        # Matrix edition
        for ts_name in STStorageTimeSeries.__args__:  # type: ignore
            ts = self.get_matrix(study, area_id, source_id, ts_name)
            self.update_matrix(study, area_id, new_id, ts_name, ts)
        return new_storage

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
            STStorageMatrix object containing the short-term storage time series.
        """
        matrix = self._get_matrix_obj(study, area_id, storage_id, ts_name)
        return STStorageMatrix(**matrix)

    def _get_matrix_obj(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
    ) -> t.MutableMapping[str, t.Any]:
        file_study = self._get_file_study(study)
        path = STORAGE_SERIES_PATH.format(area_id=area_id, storage_id=storage_id, ts_name=ts_name)
        try:
            matrix = file_study.tree.get(path.split("/"), depth=1)
        except KeyError:
            raise STStorageMatrixNotFoundError(study.id, area_id, storage_id, ts_name) from None
        return matrix

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
        self._save_matrix_obj(study, area_id, storage_id, ts_name, matrix_object)

    def _save_matrix_obj(
        self,
        study: Study,
        area_id: str,
        storage_id: str,
        ts_name: STStorageTimeSeries,
        matrix_obj: t.Dict[str, t.Any],
    ) -> None:
        file_study = self._get_file_study(study)
        path = STORAGE_SERIES_PATH.format(area_id=area_id, storage_id=storage_id, ts_name=ts_name)
        try:
            file_study.tree.save(matrix_obj, path.split("/"))
        except KeyError:
            raise STStorageMatrixNotFoundError(study.id, area_id, storage_id, ts_name) from None

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
        get_matrix_obj = functools.partial(self._get_matrix_obj, study, area_id, storage_id)

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
