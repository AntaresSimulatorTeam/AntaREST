from typing import Dict, List, Optional, Union, Any

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
    constraints: Optional[Dict[str, ConstraintDTO]]


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
                            weight = value_split[0]
                            offset = value_split[1]
                    if new_config.constraints is None:
                        new_config.constraints = {}
                    new_config.constraints[key] = ConstraintDTO(
                        id=key,
                        weight=weight,
                        offset=offset if offset is not None else None,
                        data=LinkInfoDTO(
                            area1=area1,
                            area2=area2,
                        ))
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
                            weight = value_split[0]
                            offset = value_split[1]
                    if new_config.constraints is None:
                        new_config.constraints = {}
                    new_config.constraints[key] = ConstraintDTO(
                        id=key,
                        weight=weight,
                        offset=offset if offset is not None else None,
                        data=ClusterInfoDTO(
                            area=area,
                            cluster=cluster,
                        ))
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
    def get_constraint_id(data: Union[LinkInfoDTO, ClusterInfoDTO]) -> str:
        if isinstance(data, ClusterInfoDTO):
            constraint_id = f"{data.area}.{data.cluster}"
        else:
            area1 = data.area1 if data.area1 < data.area2 else data.area2
            area2 = data.area2 if area1 == data.area1 else data.area1
            constraint_id = f"{area1}%{area2}"
        return constraint_id

    def add_new_constraint_term(
            self, study: Study, binding_constraint_id: str, new_constraint: ConstraintDTO,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if constraint is not None:
            constraint_id = BindingConstManager.get_constraint_id(new_constraint.data)
            constraints = constraint.constraints
            if constraints is None:
                constraints = {}
            if constraint_id not in constraints:
                constraints[constraint_id] = ConstraintDTO(id=constraint_id, weight=new_constraint.weight,
                                                           offset=new_constraint.offset if new_constraint.offset is not None else None,
                                                           data=new_constraint.data)
                coeffs = {}
                for constKey, coeff in constraints.items():
                    coeffs[constKey] = [coeff.weight]
                    if coeff.offset is not None:
                        coeffs[constKey].append(coeff.offset)

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
            self, study: Study, binding_constraint_id: str, data: ConstraintDTO,
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        constraint = self.get_binding_constraint(study, binding_constraint_id)
        if constraint is not None:
            constraint_id = BindingConstManager.get_constraint_id(data.data)
            constraints = constraint.constraints

            if constraints is None:
                raise NoConstraintError(study.id)

            if data.id is None or data.id not in constraints:
                raise ConstraintIdNotFoundError(study.id)

            if data.id != constraint_id:
                del constraints[data.id]

            constraints[constraint_id] = ConstraintDTO(id=constraint_id, weight=data.weight,
                                                       offset=data.offset if data.offset is not None else None, data=data.data)
            coeffs = {}
            for constKey, coeff in constraints.items():
                coeffs[constKey] = [coeff.weight]
                if coeff.offset is not None:
                    coeffs[constKey].append(coeff.offset)
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
        raise NoBindingConstraintError(study.id)
