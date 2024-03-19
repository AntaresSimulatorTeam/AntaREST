from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, validator

from antarest.core.exceptions import (
    BindingConstraintNotFoundError,
    CommandApplicationError,
    ConstraintAlreadyExistError,
    ConstraintIdNotFoundError,
    DuplicateConstraintName,
    IncoherenceBetweenMatricesLength,
    InvalidConstraintName,
    InvalidFieldForVersionError,
    MissingDataError,
    NoConstraintError,
)
from antarest.study.business.utils import AllOptionalMetaclass, execute_or_add_commands
from antarest.study.model import Study
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)
from antarest.study.storage.variantstudy.model.command.common import BindingConstraintOperator
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    BindingConstraintMatrices,
    BindingConstraintProperties,
    BindingConstraintProperties870,
    CreateBindingConstraint,
)
from antarest.study.storage.variantstudy.model.command.remove_binding_constraint import RemoveBindingConstraint
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint
from antarest.study.storage.variantstudy.model.dbmodel import VariantStudy


class AreaLinkDTO(BaseModel):
    """
    DTO for a constraint term on a link between two areas.

    Attributes:
        area1: the first area ID
        area2: the second area ID
    """

    area1: str
    area2: str

    def generate_id(self) -> str:
        """Return the constraint term ID for this link, of the form "area1%area2"."""
        # Ensure IDs are in alphabetical order and lower case
        ids = sorted((self.area1.lower(), self.area2.lower()))
        return "%".join(ids)


class AreaClusterDTO(BaseModel):
    """
    DTO for a constraint term on a cluster in an area.

    Attributes:
        area: the area ID
        cluster: the cluster ID
    """

    area: str
    cluster: str

    def generate_id(self) -> str:
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
    data: Optional[Union[AreaLinkDTO, AreaClusterDTO]]

    @validator("id")
    def id_to_lower(cls, v: Optional[str]) -> Optional[str]:
        """Ensure the ID is lower case."""
        if v is None:
            return None
        return v.lower()

    def generate_id(self) -> str:
        """Return the constraint term ID for this term based on its data."""
        if self.data is None:
            return self.id or ""
        return self.data.generate_id()


class BindingConstraintEditionModel(BaseModel, metaclass=AllOptionalMetaclass):
    group: str
    enabled: bool
    time_step: BindingConstraintFrequency
    operator: BindingConstraintOperator
    filter_year_by_year: str
    filter_synthesis: str
    comments: str
    coeffs: Dict[str, List[float]]


class BindingConstraintEdition(BindingConstraintMatrices, BindingConstraintEditionModel):
    pass


class BindingConstraintCreation(BindingConstraintMatrices, BindingConstraintProperties870):
    name: str
    coeffs: Dict[str, List[float]]


class BindingConstraintConfig(BindingConstraintProperties):
    id: str
    name: str
    constraints: Optional[List[ConstraintTermDTO]]


class BindingConstraintConfig870(BindingConstraintConfig):
    group: Optional[str] = None


BindingConstraintConfigType = Union[BindingConstraintConfig870, BindingConstraintConfig]


class BindingConstraintManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    @staticmethod
    def parse_constraint(key: str, value: str, char: str, new_config: BindingConstraintConfigType) -> bool:
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
                    data=AreaLinkDTO(
                        area1=value1,
                        area2=value2,
                    )
                    if char == "%"
                    else AreaClusterDTO(
                        area=value1,
                        cluster=value2,
                    ),
                )
            )
            return True
        return False

    @staticmethod
    def process_constraint(constraint_value: Dict[str, Any], version: int) -> BindingConstraintConfigType:
        args = {
            "id": constraint_value["id"],
            "name": constraint_value["name"],
            "enabled": constraint_value["enabled"],
            "time_step": constraint_value["type"],
            "operator": constraint_value["operator"],
            "comments": constraint_value.get("comments", None),
            "filter_year_by_year": constraint_value.get("filter-year-by-year", ""),
            "filter_synthesis": constraint_value.get("filter-synthesis", ""),
            "constraints": None,
        }
        if version < 870:
            new_config: BindingConstraintConfigType = BindingConstraintConfig(**args)
        else:
            args["group"] = constraint_value.get("group")
            new_config = BindingConstraintConfig870(**args)

        for key, value in constraint_value.items():
            if BindingConstraintManager.parse_constraint(key, value, "%", new_config):
                continue
            if BindingConstraintManager.parse_constraint(key, value, ".", new_config):
                continue
        return new_config

    @staticmethod
    def constraints_to_coeffs(
        constraint: BindingConstraintConfigType,
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
    ) -> Union[BindingConstraintConfigType, List[BindingConstraintConfigType], None]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        config_values = list(config.values())
        study_version = int(study.version)
        if constraint_id:
            try:
                index = [value["id"] for value in config_values].index(constraint_id)
                config_value = config_values[index]
                return BindingConstraintManager.process_constraint(config_value, study_version)
            except ValueError:
                return None

        binding_constraint = []
        for config_value in config_values:
            new_config = BindingConstraintManager.process_constraint(config_value, study_version)
            binding_constraint.append(new_config)
        return binding_constraint

    def validate_binding_constraint(self, study: Study, constraint_id: str) -> None:
        if int(study.version) < 870:
            return  # There's nothing to check for constraints before v8.7
        file_study = self.storage_service.get_storage(study).get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        group = next((value["group"] for value in config.values() if value["id"] == constraint_id), None)
        if not group:
            raise BindingConstraintNotFoundError(study.id)
        matrix_terms = {
            "eq": get_matrix_data(file_study, constraint_id, "eq"),
            "lt": get_matrix_data(file_study, constraint_id, "lt"),
            "gt": get_matrix_data(file_study, constraint_id, "gt"),
        }
        check_matrices_coherence(file_study, group, constraint_id, matrix_terms)

    def create_binding_constraint(
        self,
        study: Study,
        data: BindingConstraintCreation,
    ) -> BindingConstraintConfigType:
        bc_id = transform_name_to_id(data.name)
        version = int(study.version)

        if not bc_id:
            raise InvalidConstraintName(f"Invalid binding constraint name: {data.name}.")

        if bc_id in {bc.id for bc in self.get_binding_constraint(study, None)}:  # type: ignore
            raise DuplicateConstraintName(f"A binding constraint with the same name already exists: {bc_id}.")

        check_attributes_coherence(data, version)

        file_study = self.storage_service.get_storage(study).get_raw(study)
        if version >= 870:
            data.group = data.group or "default"
            matrix_terms_list = {
                "eq": data.equal_term_matrix,
                "lt": data.less_term_matrix,
                "gt": data.greater_term_matrix,
            }
            check_matrices_coherence(file_study, data.group, bc_id, matrix_terms_list)

        args = {
            "name": data.name,
            "enabled": data.enabled,
            "time_step": data.time_step,
            "operator": data.operator,
            "coeffs": data.coeffs,
            "values": data.values,
            "less_term_matrix": data.less_term_matrix,
            "equal_term_matrix": data.equal_term_matrix,
            "greater_term_matrix": data.greater_term_matrix,
            "filter_year_by_year": data.filter_year_by_year,
            "filter_synthesis": data.filter_synthesis,
            "comments": data.comments or "",
        }
        if version >= 870:
            args["group"] = data.group

        command = CreateBindingConstraint(
            **args, command_context=self.storage_service.variant_study_service.command_factory.command_context
        )

        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            command.validates_and_fills_matrices(specific_matrices=None, version=version, create=True)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Processes the constraints to add them inside the endpoint response.
        args["id"] = bc_id
        args["type"] = data.time_step
        return BindingConstraintManager.process_constraint(args, version)

    def update_binding_constraint(
        self,
        study: Study,
        binding_constraint_id: str,
        data: BindingConstraintEdition,
    ) -> BindingConstraintConfigType:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        study_version = int(study.version)
        if not isinstance(constraint, BindingConstraintConfig) and not isinstance(
            constraint, BindingConstraintConfig870
        ):
            raise BindingConstraintNotFoundError(study.id)

        check_attributes_coherence(data, study_version)

        # Because the update_binding_constraint command requires every attribute we have to fill them all.
        # This creates a `big` command even though we only updated one field.
        # fixme : Change the architecture to avoid this type of misconception
        binding_constraint_output = {
            "id": binding_constraint_id,
            "enabled": data.enabled or constraint.enabled,
            "time_step": data.time_step or constraint.time_step,
            "operator": data.operator or constraint.operator,
            "coeffs": data.coeffs or BindingConstraintManager.constraints_to_coeffs(constraint),
            "filter_year_by_year": data.filter_year_by_year or constraint.filter_year_by_year,
            "filter_synthesis": data.filter_synthesis or constraint.filter_synthesis,
            "comments": data.comments or constraint.comments,
        }
        if study_version >= 870:
            binding_constraint_output["group"] = data.group or constraint.group  # type: ignore

        args = {
            **binding_constraint_output,
            "command_context": self.storage_service.variant_study_service.command_factory.command_context,
        }
        for term in ["values", "less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
            if matrices_to_update := getattr(data, term):
                args[term] = matrices_to_update

        if data.time_step is not None and data.time_step != constraint.time_step:
            # The user changed the time step, we need to update the matrix accordingly
            args = _replace_matrices_according_to_frequency_and_version(data, study_version, args)

        command = UpdateBindingConstraint(**args)
        # Validates the matrices. Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy):
            updated_matrices = [
                term for term in ["less_term_matrix", "equal_term_matrix", "greater_term_matrix"] if getattr(data, term)
            ]
            command.validates_and_fills_matrices(
                specific_matrices=updated_matrices, version=study_version, create=False
            )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        # Processes the constraints to add them inside the endpoint response.
        binding_constraint_output["name"] = constraint.name
        binding_constraint_output["type"] = binding_constraint_output["time_step"]
        return BindingConstraintManager.process_constraint(binding_constraint_output, study_version)

    def remove_binding_constraint(self, study: Study, binding_constraint_id: str) -> None:
        command = RemoveBindingConstraint(
            id=binding_constraint_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # Needed when the study is a variant because we only append the command to the list
        if isinstance(study, VariantStudy) and not self.get_binding_constraint(study, binding_constraint_id):
            raise CommandApplicationError("Binding constraint not found")

        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def update_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term: Union[ConstraintTermDTO, str],
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)

        if not isinstance(constraint, BindingConstraintConfig) and not isinstance(constraint, BindingConstraintConfig):
            raise BindingConstraintNotFoundError(study.id)

        constraint_terms = constraint.constraints  # existing constraint terms
        if constraint_terms is None:
            raise NoConstraintError(study.id)

        term_id = term.id if isinstance(term, ConstraintTermDTO) else term
        if term_id is None:
            raise ConstraintIdNotFoundError(study.id)

        term_id_index = find_constraint_term_id(constraint_terms, term_id)
        if term_id_index < 0:
            raise ConstraintIdNotFoundError(study.id)

        if isinstance(term, ConstraintTermDTO):
            updated_term_id = term.data.generate_id() if term.data else term_id
            current_constraint = constraint_terms[term_id_index]

            constraint_terms[term_id_index] = ConstraintTermDTO(
                id=updated_term_id,
                weight=term.weight or current_constraint.weight,
                offset=term.offset,
                data=term.data or current_constraint.data,
            )
        else:
            del constraint_terms[term_id_index]

        coeffs = {term.id: [term.weight, term.offset] if term.offset else [term.weight] for term in constraint_terms}

        command = UpdateBindingConstraint(
            id=constraint.id,
            enabled=constraint.enabled,
            time_step=constraint.time_step,
            operator=constraint.operator,
            coeffs=coeffs,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            comments=constraint.comments,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def add_new_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        constraint_term: ConstraintTermDTO,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if not isinstance(constraint, BindingConstraintConfig) and not isinstance(constraint, BindingConstraintConfig):
            raise BindingConstraintNotFoundError(study.id)

        if constraint_term.data is None:
            raise MissingDataError("Add new constraint term : data is missing")

        constraint_id = constraint_term.data.generate_id()
        constraints_term = constraint.constraints or []
        if find_constraint_term_id(constraints_term, constraint_id) >= 0:
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
            comments=constraint.comments,
            filter_year_by_year=constraint.filter_year_by_year,
            filter_synthesis=constraint.filter_synthesis,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    # FIXME create a dedicated delete service
    def remove_constraint_term(
        self,
        study: Study,
        binding_constraint_id: str,
        term_id: str,
    ) -> None:
        return self.update_constraint_term(study, binding_constraint_id, term_id)


def _replace_matrices_according_to_frequency_and_version(
    data: BindingConstraintEdition, version: int, args: Dict[str, Any]
) -> Dict[str, Any]:
    if version < 870:
        if "values" not in args:
            matrix = {
                BindingConstraintFrequency.HOURLY.value: default_bc_hourly_86,
                BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_86,
                BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_86,
            }[data.time_step].tolist()
            args["values"] = matrix
    else:
        matrix = {
            BindingConstraintFrequency.HOURLY.value: default_bc_hourly_87,
            BindingConstraintFrequency.DAILY.value: default_bc_weekly_daily_87,
            BindingConstraintFrequency.WEEKLY.value: default_bc_weekly_daily_87,
        }[data.time_step].tolist()
        for term in ["less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
            if term not in args:
                args[term] = matrix
    return args


def find_constraint_term_id(constraints_term: List[ConstraintTermDTO], constraint_term_id: str) -> int:
    try:
        index = [elm.id for elm in constraints_term].index(constraint_term_id)
        return index
    except ValueError:
        return -1


def get_binding_constraint_of_a_given_group(file_study: FileStudy, group_id: str) -> List[str]:
    config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
    config_values = list(config.values())
    return [bd["id"] for bd in config_values if bd["group"] == group_id]


def check_matrices_coherence(
    file_study: FileStudy, group_id: str, binding_constraint_id: str, matrix_terms: Dict[str, Any]
) -> None:
    given_number_of_cols = set()
    for term_str, term_data in matrix_terms.items():
        if term_data:
            nb_cols = len(term_data[0])
            if nb_cols > 1:
                given_number_of_cols.add(nb_cols)
    if len(given_number_of_cols) > 1:
        raise IncoherenceBetweenMatricesLength(
            f"The matrices of {binding_constraint_id} must have the same number of columns, currently {given_number_of_cols}"
        )
    if len(given_number_of_cols) == 1:
        given_size = list(given_number_of_cols)[0]
        for bd_id in get_binding_constraint_of_a_given_group(file_study, group_id):
            for term in list(matrix_terms.keys()):
                matrix_file = file_study.tree.get(url=["input", "bindingconstraints", f"{bd_id}_{term}"])
                column_size = len(matrix_file["data"][0])
                if column_size > 1 and column_size != given_size:
                    raise IncoherenceBetweenMatricesLength(
                        f"The matrices of the group {group_id} do not have the same number of columns"
                    )


def check_attributes_coherence(
    data: Union[BindingConstraintCreation, BindingConstraintEdition], study_version: int
) -> None:
    if study_version < 870:
        if data.group:
            raise InvalidFieldForVersionError(
                f"You cannot specify a group as your study version is older than v8.7: {data.group}"
            )
        if any([data.less_term_matrix, data.equal_term_matrix, data.greater_term_matrix]):
            raise InvalidFieldForVersionError("You cannot fill a 'matrix_term' as these values refer to v8.7+ studies")
    elif data.values:
        raise InvalidFieldForVersionError("You cannot fill 'values' as it refers to the matrix before v8.7")


def get_matrix_data(file_study: FileStudy, binding_constraint_id: str, keyword: str) -> List[Any]:
    return file_study.tree.get(url=["input", "bindingconstraints", f"{binding_constraint_id}_{keyword}"])["data"]  # type: ignore
