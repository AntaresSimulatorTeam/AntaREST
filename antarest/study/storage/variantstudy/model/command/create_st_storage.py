import json
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStorageConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    GeneratorMatrixConstants,
)
from antarest.study.storage.variantstudy.business.utils import (
    strip_matrix_protocol,
    validate_matrix,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    MATCH_SIGNATURE_SEPARATOR,
    ICommand,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO
from pydantic import Field, validator, Extra
from pydantic.fields import ModelField

# noinspection SpellCheckingInspection
_MATRIX_NAMES = (
    "pmax_injection",
    "pmax_withdrawal",
    "lower_rule_curve",
    "upper_rule_curve",
    "inflows",
)

# Minimum required version.
REQUIRED_VERSION = 860

MatrixType = List[List[MatrixData]]


# noinspection SpellCheckingInspection
class CreateSTStorage(ICommand):
    """
    Command used to create a short-terme storage in an area.
    """

    class Config:
        extra = Extra.forbid

    # Overloaded parameters
    # =====================

    command_name = CommandName.CREATE_ST_STORAGE
    version = 1

    # Command parameters
    # ==================

    area_id: str = Field(description="Area ID", regex=r"[a-z0-9_(),& -]+")
    parameters: STStorageConfig
    pmax_injection: Optional[Union[MatrixType, str]] = Field(
        None,
        description="Charge capacity (modulation)",
    )
    pmax_withdrawal: Optional[Union[MatrixType, str]] = Field(
        None,
        description="Discharge capacity (modulation)",
    )
    lower_rule_curve: Optional[Union[MatrixType, str]] = Field(
        None,
        description="Lower rule curve (coefficient)",
    )
    upper_rule_curve: Optional[Union[MatrixType, str]] = Field(
        None,
        description="Upper rule curve (coefficient)",
    )
    inflows: Optional[Union[MatrixType, str]] = Field(
        None,
        description="Inflows (MW)",
    )

    @property
    def storage_id(self) -> str:
        """The normalized version of the storage's name used as the ID."""
        return self.parameters.id

    @property
    def storage_name(self) -> str:
        """The label representing the name of the storage for the user."""
        return self.parameters.name

    @validator(*_MATRIX_NAMES, always=True)
    def register_matrix(
        cls,
        v: Optional[Union[MatrixType, str]],
        values: Dict[str, Any],
        field: ModelField,
    ) -> Optional[Union[MatrixType, str]]:
        """
        Validates a matrix array or link, and store the matrix array in the matrix repository.

        This method is used to validate the matrix array or link provided as input.

        - If the input is `None`, it retrieves a default matrix from the
          generator matrix constants.
        - If the input is a string, it validates the matrix link.
        - If the input is a list of lists, it validates the matrix values
          and creates the corresponding matrix link.

        Args:
            v: The matrix array or link to be validated and registered.
            values: A dictionary containing additional values used for validation.
            field: The field being validated.

        Returns:
            The ID of the validated and stored matrix prefixed by "matrix://".

        Raises:
            ValueError: If the matrix has an invalid shape, contains NaN values,
                or violates specific constraints.
            TypeError: If the input datatype is not supported.
        """
        if v is None:
            # use an already-registered default matrix
            constants: GeneratorMatrixConstants
            constants = values["command_context"].generator_matrix_constants
            # Directly access the methods instead of using `getattr` for maintainability
            methods = {
                "pmax_injection": constants.get_st_storage_pmax_injection,
                "pmax_withdrawal": constants.get_st_storage_pmax_withdrawal,
                "lower_rule_curve": constants.get_st_storage_lower_rule_curve,
                "upper_rule_curve": constants.get_st_storage_upper_rule_curve,
                "inflows": constants.get_st_storage_inflows,
            }
            method = methods[field.name]
            return cast(str, method())
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, values)
        if isinstance(v, list):
            # Check the matrix values and create the corresponding matrix link
            array = np.array(v, dtype=np.float64)
            if array.shape != (8760, 1):
                raise ValueError(
                    f"Invalid matrix shape {array.shape}, expected (8760, 1)"
                )
            if np.isnan(array).any():
                raise ValueError("Matrix values cannot contain NaN")
            # All matrices except "inflows" are constrained between 0 and 1
            constrained = set(_MATRIX_NAMES) - {"inflows"}
            if field.name in constrained and (
                np.any(array < 0) or np.any(array > 1)
            ):
                raise ValueError("Matrix values should be between 0 and 1")
            v = cast(MatrixType, array.tolist())
            return validate_matrix(v, values)
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: add the short-term storage in the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary of extra data is `{"storage_id": storage_id}`.
        """

        # Check if the study version is above the minimum required version.
        version = study_data.version
        if version < REQUIRED_VERSION:
            return (
                CommandOutput(
                    status=False,
                    message=(
                        f"Invalid study version {version},"
                        f" at least version {REQUIRED_VERSION} is required."
                    ),
                ),
                {},
            )

        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist in the study configuration.",
                ),
                {},
            )
        area: Area = study_data.areas[self.area_id]

        # Check if the short-term storage already exists in the area
        if any(s.id == self.storage_id for s in area.st_storages):
            return (
                CommandOutput(
                    status=False,
                    message=(
                        f"Short-term storage '{self.storage_name}' already exists"
                        f" in the area '{self.area_id}'."
                    ),
                ),
                {},
            )

        # Create a new short-term storage and add it to the area
        area.st_storages.append(self.parameters)

        return (
            CommandOutput(
                status=True,
                message=(
                    f"Short-term st_storage '{self.storage_name}' successfully added"
                    f" to area '{self.area_id}'."
                ),
            ),
            {"storage_id": self.storage_id},
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Saves the changes made to the storage configurations.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output

        # Fill-in the "list.ini" file with the parameters
        config = study_data.tree.get(
            ["input", "st-storage", "clusters", self.area_id, "list"]
        )
        config[self.storage_id] = json.loads(
            self.parameters.json(by_alias=True)
        )

        new_data: JSON = {
            "input": {
                "st-storage": {
                    "clusters": {self.area_id: {"list": config}},
                    "series": {
                        self.area_id: {
                            self.storage_id: {
                                attr: getattr(self, attr)
                                for attr in _MATRIX_NAMES
                            }
                        }
                    },
                }
            }
        }
        study_data.tree.save(new_data)

        return output

    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        parameters = json.loads(self.parameters.json(by_alias=True))
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "parameters": parameters,
                **{
                    attr: strip_matrix_protocol(getattr(self, attr))
                    for attr in _MATRIX_NAMES
                },
            },
        )

    def match_signature(self) -> str:
        """Returns the command signature."""
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_id
            + MATCH_SIGNATURE_SEPARATOR
            + self.storage_id
        )

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        """
        Checks if the current instance matches another `ICommand` object.

        Args:
            other: Another `ICommand` object to compare against.
            equal: Flag indicating whether to perform a deep comparison.

        Returns:
            bool: `True` if the current instance matches the other object, `False` otherwise.
        """
        if not isinstance(other, CreateSTStorage):
            return False
        if equal:
            # Deep comparison
            return self.__eq__(other)
        else:
            return (
                self.area_id == other.area_id
                and self.storage_id == other.storage_id
            )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        """
        Creates a list of commands representing the differences between
        the current instance and another `ICommand` object.

        Args:
            other: Another ICommand object to compare against.

        Returns:
            A list of commands representing the differences between
            the two `ICommand` objects.
        """
        from antarest.study.storage.variantstudy.model.command.replace_matrix import (
            ReplaceMatrix,
        )
        from antarest.study.storage.variantstudy.model.command.update_config import (
            UpdateConfig,
        )

        other = cast(CreateSTStorage, other)
        commands: List[ICommand] = [
            ReplaceMatrix(
                target=f"input/st-storage/series/{self.area_id}/{self.storage_id}/{attr}",
                matrix=strip_matrix_protocol(getattr(other, attr)),
                command_context=self.command_context,
            )
            for attr in _MATRIX_NAMES
            if getattr(self, attr) != getattr(other, attr)
        ]
        if self.parameters != other.parameters:
            data: Dict[str, Any] = json.loads(
                other.parameters.json(by_alias=True)
            )
            commands.append(
                UpdateConfig(
                    target=f"input/st-storage/clusters/{self.area_id}/list/{self.storage_id}",
                    data=data,
                    command_context=self.command_context,
                )
            )
        return commands

    def get_inner_matrices(self) -> List[str]:
        """
        Retrieves the list of matrix IDs.
        """
        matrices: List[str] = [
            strip_matrix_protocol(getattr(self, attr))
            for attr in _MATRIX_NAMES
        ]
        return matrices
