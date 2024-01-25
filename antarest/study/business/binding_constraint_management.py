from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator

from antarest.core.exceptions import (
    ConstraintAlreadyExistError,
    ConstraintIdNotFoundError,
    DuplicateConstraintName,
    InvalidConstraintName,
    MissingDataError,
    NoBindingConstraintError,
    NoConstraintError,
)
from antarest.matrixstore.model import MatrixData
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series import (
    default_bc_hourly,
    default_bc_weekly_daily,
)
from antarest.study.storage.variantstudy.model.command.common import BindingConstraintOperator
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    BindingConstraintProperties,
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint


class LinkInfoDTO(BaseModel):
    """
    DTO for a constraint term on a link between two areas.

    Attributes:
        area1: the first area ID
        area2: the second area ID
    """

    area1: str
    area2: str

    def calc_term_id(self) -> str:
        """Return the constraint term ID for this link, of the form "area1%area2"."""
        # Ensure IDs are in alphabetical order and lower case
        ids = sorted((self.area1.lower(), self.area2.lower()))
        return "%".join(ids)


class ClusterInfoDTO(BaseModel):
    """
    DTO for a constraint term on a cluster in an area.

    Attributes:
        area: the area ID
        cluster: the cluster ID
    """

    area: str
    cluster: str

    def calc_term_id(self) -> str:
        """Return the constraint term ID for this Area/cluster constraint, of the form "area.cluster"."""
        # Ensure IDs are in lower case
        ids = [self.area.lower(), self.cluster.lower()]
        return ".".join(ids)


class ConstraintTermDTO(BaseModel):
    """
    DTO for a constraint term.

    Attributes:
        id: the constraint term ID, of the form "area1%area2" or "area.cluster".
        weight: the constraint term weight, if any.
        offset: the constraint term offset, if any.
        data: the constraint term data (link or cluster), if any.
    """

    id: Optional[str]
    weight: Optional[float]
    offset: Optional[float]
    data: Optional[Union[LinkInfoDTO, ClusterInfoDTO]]

    @validator("id")
    def id_to_lower(cls, v: Optional[str]) -> Optional[str]:
        """Ensure the ID is lower case."""
        if v is None:
            return None
        return v.lower()

    def calc_term_id(self) -> str:
        """Return the constraint term ID for this term based on its data."""
        if self.data is None:
            return self.id or ""
        return self.data.calc_term_id()


class UpdateBindingConstProps(BaseModel):
    key: str
    value: Any


class BindingConstraintPropertiesWithName(BindingConstraintProperties):
    name: str


class BindingConstraintDTO(BaseModel):
    id: str
    name: str
    enabled: bool = True
    time_step: BindingConstraintFrequency
    operator: BindingConstraintOperator
    values: Optional[Union[List[List[MatrixData]], str]] = None
    comments: Optional[str] = None
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None
    constraints: Optional[List[ConstraintTermDTO]]


class BindingConstraintManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    @staticmethod
    def parse_constraint(key: str, value: str, char: str, new_config: BindingConstraintDTO) -> bool:
        split = key.split(char)
        if len(split) == 2:
            value1 = split[0]
            value2 = split[1]
            weight = 0.0
            offset = None
            try:
                weight = float(value)
            except ValueError:
                weight_and_offset = value.split("%")
                if len(weight_and_offset) == 2:
                    weight = float(weight_and_offset[0])
                    offset = float(weight_and_offset[1])
            if new_config.constraints is None:
                new_config.constraints = []
            new_config.constraints.append(
                ConstraintTermDTO(
                    id=key,
                    weight=weight,
                    offset=offset if offset is not None else None,
                    data=LinkInfoDTO(
                        area1=value1,
                        area2=value2,
                    )
                    if char == "%"
                    else ClusterInfoDTO(
                        area=value1,
                        cluster=value2,
                    ),
                )
            )
            return True
        return False

    @staticmethod
    def process_constraint(
        constraint_value: Dict[str, Any],
    ) -> BindingConstraintDTO:
        new_config: BindingConstraintDTO = BindingConstraintDTO(
            id=constraint_value["id"],
            name=constraint_value["name"],
            enabled=constraint_value["enabled"],
            time_step=constraint_value["type"],
            operator=constraint_value["operator"],
            comments=constraint_value.get("comments", None),
            filter_year_by_year=constraint_value.get("filter-year-by-year", ""),
            filter_synthesis=constraint_value.get("filter-synthesis", ""),
            constraints=None,
        )
        for key, value in constraint_value.items():
            if BindingConstraintManager.parse_constraint(key, value, "%", new_config):
                continue
            if BindingConstraintManager.parse_constraint(key, value, ".", new_config):
                continue
        return new_config

    @staticmethod
    def constraints_to_coeffs(
        constraint: BindingConstraintDTO,
    ) -> Dict[str, List[float]]:
        coeffs: Dict[str, List[float]] = {}
        if constraint.constraints is not None:
            for term in constraint.constraints:
                if term.id is not None and term.weight is not None:
                    coeffs[term.id] = [term.weight]
                    if term.offset is not None:
                        coeffs[term.id].append(term.offset)

        return coeffs

    def get_binding_constraint(
        self, study: Study, constraint_id: Optional[str]
    ) -> Union[BindingConstraintDTO, List[BindingConstraintDTO], None]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        config_values = list(config.values())
        if constraint_id:
            try:
                index = [value["id"] for value in config_values].index(constraint_id)
                config_value = config_values[index]
                return BindingConstraintManager.process_constraint(config_value)
            except ValueError:
                return None

        binding_constraint = []
        for config_value in config_values:
            new_config = BindingConstraintManager.process_constraint(config_value)
            binding_constraint.append(new_config)
        return binding_constraint

    def create_binding_constraint(
        self,
        study: Study,
        data: BindingConstraintPropertiesWithName,
    ) -> None:
        bc_id = transform_name_to_id(data.name)

        if not bc_id:
            raise InvalidConstraintName(f"Invalid binding constraint name: {data.name}.")

        file_study = self.storage_service.get_storage(study).get_raw(study)
        binding_constraints = self.get_binding_constraint(study, None)
        existing_ids = {bc.id for bc in binding_constraints}  # type: ignore

        if bc_id in existing_ids:
            raise DuplicateConstraintName(f"A binding constraint with the same name already exists: {bc_id}.")

        command = CreateBindingConstraint(
            name=data.name,
            enabled=data.enabled,
            time_step=data.time_step,
            operator=data.operator,
            coeffs=data.coeffs,
            values=data.values,
            filter_year_by_year=data.filter_year_by_year,
            filter_synthesis=data.filter_synthesis,
            comments=data.comments or "",
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def update_binding_constraint(
        self,
        study: Study,
        binding_constraint_id: str,
        data: UpdateBindingConstProps,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if not isinstance(constraint, BindingConstraintDTO):
            raise NoBindingConstraintError(study.id)

        if data.key == "time_step" and data.value != constraint.time_step:
            # The user changed the time step, we need to update the matrix accordingly
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily,
            }[data.value].tolist()
        else:
            # The user changed another property, we keep the matrix as it is
            matrix = constraint.values

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=data.value if data.key == "enabled" else constraint.enabled,
            time_step=data.value if data.key == "time_step" else constraint.time_step,
            operator=data.value if data.key == "operator" else constraint.operator,
            coeffs=BindingConstraintManager.constraints_to_coeffs(constraint),
            values=matrix,
            filter_year_by_year=data.value if data.key == "filterByYear" else constraint.filter_year_by_year,
            filter_synthesis=data.value if data.key == "filterSynthesis" else constraint.filter_synthesis,
            comments=data.value if data.key == "comments" else constraint.comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    @staticmethod
    def find_constraint_term_id(constraints_term: List[ConstraintTermDTO], constraint_term_id: str) -> int:
        try:
            index = [elm.id for elm in constraints_term].index(constraint_term_id)
            return index
        except ValueError:
            return -1

    @staticmethod
    def get_constraint_id(data: Union[LinkInfoDTO, ClusterInfoDTO]) -> str:
        return data.calc_term_id()

    def add_new_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        constraint_term: ConstraintTermDTO,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if not isinstance(constraint, BindingConstraintDTO):
            # todo: should be renamed 'BindingConstraintNotFoundError'
            raise NoBindingConstraintError(study.id)

        if constraint_term.data is None:
            raise MissingDataError("Add new constraint term : data is missing")

        constraint_id = constraint_term.data.calc_term_id()
        constraints_term = constraint.constraints or []
        if BindingConstraintManager.find_constraint_term_id(constraints_term, constraint_id) >= 0:
            raise ConstraintAlreadyExistError(study.id)

        constraints_term.append(
            ConstraintTermDTO(
                id=constraint_id,
                weight=constraint_term.weight if constraint_term.weight is not None else 0.0,
                offset=constraint_term.offset,
                data=constraint_term.data,
            )
        )
        coeffs = {}
        for term in constraints_term:
            coeffs[term.id] = [term.weight]
            if term.offset is not None:
                coeffs[term.id].append(term.offset)

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=constraint.enabled,
            time_step=constraint.time_step,
            operator=constraint.operator,
            coeffs=coeffs,
            values=constraint.values,
            comments=constraint.comments,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def update_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        data: Union[ConstraintTermDTO, str],
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if not isinstance(constraint, BindingConstraintDTO):
            # todo: should be renamed 'BindingConstraintNotFoundError'
            raise NoBindingConstraintError(study.id)

        constraints = constraint.constraints
        if constraints is None:
            # todo: should be renamed 'ConstraintTermNotFoundError'
            raise NoConstraintError(study.id)

        data_id = data.id if isinstance(data, ConstraintTermDTO) else data
        if data_id is None:
            raise ConstraintIdNotFoundError(study.id)

        data_term_index = BindingConstraintManager.find_constraint_term_id(constraints, data_id)
        if data_term_index < 0:
            raise ConstraintIdNotFoundError(study.id)

        if isinstance(data, ConstraintTermDTO):
            constraint_id = data_id if data.data is None else data.data.calc_term_id()
            current_constraint = constraints[data_term_index]
            constraints.append(
                ConstraintTermDTO(
                    id=constraint_id,
                    weight=data.weight if data.weight is not None else current_constraint.weight,
                    offset=data.offset,
                    data=data.data if data.data is not None else current_constraint.data,
                )
            )
            del constraints[data_term_index]
        else:
            del constraints[data_term_index]

        coeffs = {}
        for term in constraints:
            coeffs[term.id] = [term.weight]
            if term.offset is not None:
                coeffs[term.id].append(term.offset)

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=constraint.enabled,
            time_step=constraint.time_step,
            operator=constraint.operator,
            coeffs=coeffs,
            values=constraint.values,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            comments=constraint.comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def remove_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term_id: str,
    ) -> None:
        return self.update_constraint_term(study, binding_constraint_id, term_id)
