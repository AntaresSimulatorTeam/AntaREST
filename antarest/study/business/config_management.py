from enum import Enum
from functools import reduce
from typing import Dict, Any, List, Union

from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import (
    RawStudy,
    Study,
)
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class OutputVariableBase(str, Enum):
    OV_COST = "OV. COST"
    OP_COST = "OP. COST"
    MRG_PRICE = "MRG. PRICE"
    CO2_EMIS = "CO2 EMIS."
    DTG_BY_PLANT = "DTG by plant"
    BALANCE = "BALANCE"
    ROW_BAL = "ROW BAL."
    PSP = "PSP"
    MISC_NDG = "MISC. NDG"
    LOAD = "LOAD"
    H_ROR = "H. ROR"
    WIND = "WIND"
    SOLAR = "SOLAR"
    NUCLEAR = "NUCLEAR"
    LIGNITE = "LIGNITE"
    COAL = "COAL"
    GAS = "GAS"
    OIL = "OIL"
    MIX_FUEL = "MIX. FUEL"
    MISC_DTG = "MISC. DTG"
    H_STOR = "H. STOR"
    H_PUMP = "H. PUMP"
    H_LEV = "H. LEV"
    H_INFL = "H. INFL"
    H_OVFL = "H. OVFL"
    H_VAL = "H. VAL"
    H_COST = "H. COST"
    UNSP_ENRG = "UNSP. ENRG"
    SPIL_ENRG = "SPIL. ENRG"
    LOLD = "LOLD"
    LOLP = "LOLP"
    AVL_DTG = "AVL DTG"
    DTG_MRG = "DTG MRG"
    MAX_MRG = "MAX MRG"
    NP_COST = "NP COST"
    NP_Cost_by_plant = "NP Cost by plant"
    NODU = "NODU"
    NODU_by_plant = "NODU by plant"
    FLOW_LIN = "FLOW LIN."
    UCAP_LIN = "UCAP LIN."
    LOOP_FLOW = "LOOP FLOW"
    FLOW_QUAD = "FLOW QUAD."
    CONG_FEE_ALG = "CONG. FEE (ALG.)"
    CONG_FEE_ABS = "CONG. FEE (ABS.)"
    MARG_COST = "MARG. COST"
    CONG_PROD_PLUS = "CONG. PROD +"
    CONG_PROD_MINUS = "CONG. PROD -"
    HURDLE_COST = "HURDLE COST"


class OutputVariable810(str, Enum):
    RES_GENERATION_BY_PLANT = "RES generation by plant"
    MISC_DTG_2 = "MISC. DTG 2"
    MISC_DTG_3 = "MISC. DTG 3"
    MISC_DTG_4 = "MISC. DTG 4"
    WIND_OFFSHORE = "WIND OFFSHORE"
    WIND_ONSHORE = "WIND ONSHORE"
    SOLAR_CONCRT = "SOLAR CONCRT."
    SOLAR_PV = "SOLAR PV"
    SOLAR_ROOFT = "SOLAR ROOFT"
    RENW_1 = "RENW. 1"
    RENW_2 = "RENW. 2"
    RENW_3 = "RENW. 3"
    RENW_4 = "RENW. 4"


OutputVariable = Union[OutputVariableBase, OutputVariable810]
OUTPUT_VARIABLE_LIST: List[str] = [var.value for var in OutputVariableBase] + [
    var.value for var in OutputVariable810
]


class ConfigManager:
    def __init__(
        self,
        storage_service: StudyStorageService,
    ) -> None:
        self.storage_service = storage_service

    @staticmethod
    def get_output_variables(study: Study) -> List[str]:
        version = int(study.version)
        if version < 810:
            return [var.value for var in OutputVariableBase]
        return OUTPUT_VARIABLE_LIST

    def get_thematic_trimming(self, study: Study) -> Dict[str, bool]:
        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)
        config = file_study.tree.get(["settings", "generaldata"])
        trimming_config = config.get("variables selection", None)
        variable_list = self.get_output_variables(study)
        if trimming_config:
            if trimming_config.get("selected_vars_reset", True):
                return {
                    var: var not in trimming_config.get("select_var -", [])
                    for var in variable_list
                }
            else:
                return {
                    var: var in trimming_config.get("select_var +", [])
                    for var in variable_list
                }
        return {var: True for var in variable_list}

    def set_thematic_trimming(
        self, study: Study, state: Dict[str, bool]
    ) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        state_by_active: Dict[bool, List[str]] = reduce(
            lambda agg, output: self._agg_states(agg, output, state),
            state.keys(),
            {True: [], False: []},
        )
        config_data: Dict[str, Any]
        if len(state_by_active[True]) > len(state_by_active[False]):
            config_data = {"select_var -": state_by_active[False]}
        else:
            config_data = {
                "selected_vars_reset": True,
                "select_var +": state_by_active[True],
            }
        command = UpdateConfig(
            target="settings/generaldata/variables selection",
            data=config_data,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
        )
        execute_or_add_commands(
            study, file_study, [command], self.storage_service
        )

    @staticmethod
    def _agg_states(
        state: Dict[bool, List[str]],
        key: str,
        ref: Dict[str, bool],
    ) -> Dict[bool, List[str]]:
        state[ref[key]].append(key)
        return state
