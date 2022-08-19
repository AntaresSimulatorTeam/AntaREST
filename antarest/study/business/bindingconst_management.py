from typing import List, Optional, Union

from pydantic import BaseModel

from antarest.core.exceptions import NoConstraintError, ConstraintAlreadyExistError, ConstraintIdNotFoundError, \
    NoBindingConstraintError
from antarest.matrixstore.model import MatrixData
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import (
    Study,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.common import TimeStep, BindingConstraintOperator
from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint


class LinkInfoDTO(BaseModel):
    area1: str
    area2: str


class ClusterInfoDTO(BaseModel):
    area: str
    cluster: str


class ConstraintDTO(BaseModel):
    id: Optional[str]
    weight: float
    offset: Optional[float]
    data: Union[LinkInfoDTO, ClusterInfoDTO]


class BindingConstDTO(BaseModel):
    id: str
    name: str
    enabled: bool = True
    time_step: TimeStep
    operator: BindingConstraintOperator
    values: Optional[Union[List[List[MatrixData]], str]] = None
    comments: Optional[str] = None
    constraints: Optional[List[ConstraintDTO]]


class BindingConstManager:
    def __init__(
            self,
            storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    def get_binding_constraint_list(self, study: Study) -> List[BindingConstDTO]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        binding_constraint = []
        for config_value in config.values():
            new_config: BindingConstDTO = BindingConstDTO(
                id=config_value["id"],
                name=config_value["name"],
                enabled=config_value["enabled"],
                time_step=TimeStep.from_str(config_value["type"]),
                operator=config_value["operator"],
                comments=config_value["comments"] if "comments" in config_value else None,
                constraints=None
            )

            for key, value in config_value.items():
                split = key.split("%")
                if len(split) == 2:
                    area1 = split[0]
                    area2 = split[1]
                    weight = 0.0
                    offset = None
                    try:
                        weight = float(value)
                    except ValueError:
                        value_split = value.split("%")
                        if len(value_split) == 2:
                            weight = float(value_split[0])
                            offset = float(value_split[1])
                    if new_config.constraints is None:
                        new_config.constraints = []
                    new_config.constraints.append(ConstraintDTO(
                        id=key,
                        weight=weight,
                        offset=offset if offset is not None else None,
                        data=LinkInfoDTO(
                            area1=area1,
                            area2=area2,
                        )))
                    continue

                split = key.split(".")
                if len(split) == 2:
                    area = split[0]
                    cluster = split[1]
                    weight = 0
                    offset = None
                    try:
                        weight = float(value)
                    except ValueError:
                        value_split = value.split("%")
                        if len(value_split) == 2:
                            weight = float(value_split[0])
                            offset = float(value_split[1])
                    if new_config.constraints is None:
                        new_config.constraints = []
                    new_config.constraints.append(ConstraintDTO(
                        id=key,
                        weight=weight,
                        offset=offset if offset is not None else None,
                        data=ClusterInfoDTO(
                            area=area,
                            cluster=cluster,
                        )))
                    continue

            binding_constraint.append(new_config)
        return binding_constraint

    def get_binding_constraint(self, study: Study, binding_constraint_id: str) -> Optional[BindingConstDTO]:
        bc = self.get_binding_constraint_list(study)
        try:
            index = [elm.id for elm in bc].index(binding_constraint_id)
            return bc[index]
        except ValueError:
            return None
        return None

    @staticmethod
    def find_constraint_term_id(constraints: List[ConstraintDTO], constraint_id: str) -> int:
        try:
            index = [elm.id for elm in constraints].index(constraint_id)
            return index
        except ValueError:
            return -1
        return -1

    @staticmethod
    def get_constraint_id(data: Union[LinkInfoDTO, ClusterInfoDTO]) -> str:
        if isinstance(data, ClusterInfoDTO):
            constraint_id = f"{data.area}.{data.cluster}"
        else:
            area1 = data.area1 if data.area1 < data.area2 else data.area2
            area2 = data.area2 if area1 == data.area1 else data.area1
            constraint_id = f"{area1}%{area2}"
        return constraint_id

    # def find_first_available_new_term(self, constraints: Optional[List[ConstraintDTO]]) -> None:
    #    bc = 6

    def add_new_constraint_term(
            self, study: Study, binding_constraint_id: str, new_constraint: Optional[ConstraintDTO],
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if constraint is not None:

            if new_constraint is None:
                return self.find_first_available_new_term(self.get_binding_constraint_list(study),
                                                          constraint.constraints)
            else:
                constraint_id = BindingConstManager.get_constraint_id(new_constraint.data)
                constraints = constraint.constraints
                if constraints is None:
                    constraints = []
                if BindingConstManager.find_constraint_term_id(constraints, constraint_id) < 0:
                    constraints.append(ConstraintDTO(id=constraint_id, weight=new_constraint.weight,
                                                     offset=new_constraint.offset if new_constraint.offset is not None else None,
                                                     data=new_constraint.data))
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
                        comments=constraint.comments,
                        command_context=self.storage_service.variant_study_service.command_factory.command_context,
                    )
                    execute_or_add_commands(
                        study, file_study, [command], self.storage_service
                    )
                    return None
                raise ConstraintAlreadyExistError(study.id)
        raise NoBindingConstraintError(study.id)

    def update_constraint_term(
            self, study: Study, binding_constraint_id: str, data: Union[ConstraintDTO, str],
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if constraint is not None:
            constraints = constraint.constraints
            if constraints is None:
                raise NoConstraintError(study.id)

            data_id = data.id if isinstance(data, ConstraintDTO) else data
            if data_id is None:
                raise ConstraintIdNotFoundError(study.id)

            data_term_index = BindingConstManager.find_constraint_term_id(constraints, data_id)
            if data_term_index < 0:
                raise ConstraintIdNotFoundError(study.id)

            if isinstance(data, ConstraintDTO):
                constraint_id = BindingConstManager.get_constraint_id(data.data)
                if data_id != constraint_id:
                    del constraints[data_term_index]
                constraints.append(ConstraintDTO(id=constraint_id, weight=data.weight,
                                                 offset=data.offset if data.offset is not None else None,
                                                 data=data.data))
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
                comments=constraint.comments,
                command_context=self.storage_service.variant_study_service.command_factory.command_context,
            )
            execute_or_add_commands(
                study, file_study, [command], self.storage_service
            )
            # self.storage_service.event_bus.push(
            #    Event(
            #        type=EventType.STUDY_DATA_EDITED,
            #        payload=study.to_json_summary(),
            #        permissions=create_permission_from_study(study),
            #    )
            # )
            return None
        raise NoBindingConstraintError(study.id)

    def remove_constraint_term(
            self, study: Study, binding_constraint_id: str, term_id: str,
    ) -> None:
        return self.update_constraint_term(study, binding_constraint_id, term_id)
