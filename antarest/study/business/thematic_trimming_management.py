from typing import Optional, Dict, Any, List

from pydantic.types import StrictBool

from antarest.study.business.utils import (
    FormFieldsBaseModel,
    FieldInfo,
    GENERAL_DATA_PATH,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import (
    UpdateConfig,
)


class ThematicTrimmingFormFields(FormFieldsBaseModel):
    ov_cost: Optional[StrictBool]
    op_cost: Optional[StrictBool]
    mrg_price: Optional[StrictBool]
    co2_emis: Optional[StrictBool]
    dtg_by_plant: Optional[StrictBool]
    balance: Optional[StrictBool]
    row_bal: Optional[StrictBool]
    psp: Optional[StrictBool]
    misc_ndg: Optional[StrictBool]
    load: Optional[StrictBool]
    h_ror: Optional[StrictBool]
    wind: Optional[StrictBool]
    solar: Optional[StrictBool]
    nuclear: Optional[StrictBool]
    lignite: Optional[StrictBool]
    coal: Optional[StrictBool]
    gas: Optional[StrictBool]
    oil: Optional[StrictBool]
    mix_fuel: Optional[StrictBool]
    misc_dtg: Optional[StrictBool]
    h_stor: Optional[StrictBool]
    h_pump: Optional[StrictBool]
    h_lev: Optional[StrictBool]
    h_infl: Optional[StrictBool]
    h_ovfl: Optional[StrictBool]
    h_val: Optional[StrictBool]
    h_cost: Optional[StrictBool]
    unsp_enrg: Optional[StrictBool]
    spil_enrg: Optional[StrictBool]
    lold: Optional[StrictBool]
    lolp: Optional[StrictBool]
    avl_dtg: Optional[StrictBool]
    dtg_mrg: Optional[StrictBool]
    max_mrg: Optional[StrictBool]
    np_cost: Optional[StrictBool]
    np_cost_by_plant: Optional[StrictBool]
    nodu: Optional[StrictBool]
    nodu_by_plant: Optional[StrictBool]
    flow_lin: Optional[StrictBool]
    ucap_lin: Optional[StrictBool]
    loop_flow: Optional[StrictBool]
    flow_quad: Optional[StrictBool]
    cong_fee_alg: Optional[StrictBool]
    cong_fee_abs: Optional[StrictBool]
    marg_cost: Optional[StrictBool]
    cong_prod_plus: Optional[StrictBool]
    cong_prod_minus: Optional[StrictBool]
    hurdle_cost: Optional[StrictBool]
    # For study versions >= 810
    res_generation_by_plant: Optional[StrictBool]
    misc_dtg_2: Optional[StrictBool]
    misc_dtg_3: Optional[StrictBool]
    misc_dtg_4: Optional[StrictBool]
    wind_offshore: Optional[StrictBool]
    wind_onshore: Optional[StrictBool]
    solar_concrt: Optional[StrictBool]
    solar_pv: Optional[StrictBool]
    solar_rooft: Optional[StrictBool]
    renw_1: Optional[StrictBool]
    renw_2: Optional[StrictBool]
    renw_3: Optional[StrictBool]
    renw_4: Optional[StrictBool]
    # For study versions >= 830
    dens: Optional[StrictBool]
    profit: Optional[StrictBool]


FIELDS_INFO: Dict[str, FieldInfo] = {
    "ov_cost": {"path": "OV. COST", "default_value": True},
    "op_cost": {"path": "OP. COST", "default_value": True},
    "mrg_price": {"path": "MRG. PRICE", "default_value": True},
    "co2_emis": {"path": "CO2 EMIS.", "default_value": True},
    "dtg_by_plant": {"path": "DTG by plant", "default_value": True},
    "balance": {"path": "BALANCE", "default_value": True},
    "row_bal": {"path": "ROW BAL.", "default_value": True},
    "psp": {"path": "PSP", "default_value": True},
    "misc_ndg": {"path": "MISC. NDG", "default_value": True},
    "load": {"path": "LOAD", "default_value": True},
    "h_ror": {"path": "H. ROR", "default_value": True},
    "wind": {"path": "WIND", "default_value": True},
    "solar": {"path": "SOLAR", "default_value": True},
    "nuclear": {"path": "NUCLEAR", "default_value": True},
    "lignite": {"path": "LIGNITE", "default_value": True},
    "coal": {"path": "COAL", "default_value": True},
    "gas": {"path": "GAS", "default_value": True},
    "oil": {"path": "OIL", "default_value": True},
    "mix_fuel": {"path": "MIX. FUEL", "default_value": True},
    "misc_dtg": {"path": "MISC. DTG", "default_value": True},
    "h_stor": {"path": "H. STOR", "default_value": True},
    "h_pump": {"path": "H. PUMP", "default_value": True},
    "h_lev": {"path": "H. LEV", "default_value": True},
    "h_infl": {"path": "H. INFL", "default_value": True},
    "h_ovfl": {"path": "H. OVFL", "default_value": True},
    "h_val": {"path": "H. VAL", "default_value": True},
    "h_cost": {"path": "H. COST", "default_value": True},
    "unsp_enrg": {"path": "UNSP. ENRG", "default_value": True},
    "spil_enrg": {"path": "SPIL. ENRG", "default_value": True},
    "lold": {"path": "LOLD", "default_value": True},
    "lolp": {"path": "LOLP", "default_value": True},
    "avl_dtg": {"path": "AVL DTG", "default_value": True},
    "dtg_mrg": {"path": "DTG MRG", "default_value": True},
    "max_mrg": {"path": "MAX MRG", "default_value": True},
    "np_cost": {"path": "NP COST", "default_value": True},
    "np_cost_by_plant": {"path": "NP Cost by plant", "default_value": True},
    "nodu": {"path": "NODU", "default_value": True},
    "nodu_by_plant": {"path": "NODU by plant", "default_value": True},
    "flow_lin": {"path": "FLOW LIN.", "default_value": True},
    "ucap_lin": {"path": "UCAP LIN.", "default_value": True},
    "loop_flow": {"path": "LOOP FLOW", "default_value": True},
    "flow_quad": {"path": "FLOW QUAD.", "default_value": True},
    "cong_fee_alg": {"path": "CONG. FEE (ALG.)", "default_value": True},
    "cong_fee_abs": {"path": "CONG. FEE (ABS.)", "default_value": True},
    "marg_cost": {"path": "MARG. COST", "default_value": True},
    "cong_prod_plus": {"path": "CONG. PROD +", "default_value": True},
    "cong_prod_minus": {"path": "CONG. PROD -", "default_value": True},
    "hurdle_cost": {"path": "HURDLE COST", "default_value": True},
    "res_generation_by_plant": {
        "path": "RES generation by plant",
        "default_value": True,
        "start_version": 810,
    },
    "misc_dtg_2": {
        "path": "MISC. DTG 2",
        "default_value": True,
        "start_version": 810,
    },
    "misc_dtg_3": {
        "path": "MISC. DTG 3",
        "default_value": True,
        "start_version": 810,
    },
    "misc_dtg_4": {
        "path": "MISC. DTG 4",
        "default_value": True,
        "start_version": 810,
    },
    "wind_offshore": {
        "path": "WIND OFFSHORE",
        "default_value": True,
        "start_version": 810,
    },
    "wind_onshore": {
        "path": "WIND ONSHORE",
        "default_value": True,
        "start_version": 810,
    },
    "solar_concrt": {
        "path": "SOLAR CONCRT.",
        "default_value": True,
        "start_version": 810,
    },
    "solar_pv": {
        "path": "SOLAR PV",
        "default_value": True,
        "start_version": 810,
    },
    "solar_rooft": {
        "path": "SOLAR ROOFT",
        "default_value": True,
        "start_version": 810,
    },
    "renw_1": {"path": "RENW. 1", "default_value": True, "start_version": 810},
    "renw_2": {"path": "RENW. 2", "default_value": True, "start_version": 810},
    "renw_3": {"path": "RENW. 3", "default_value": True, "start_version": 810},
    "renw_4": {"path": "RENW. 4", "default_value": True, "start_version": 810},
    "dens": {"path": "DENS", "default_value": True, "start_version": 830},
    "profit": {"path": "Profit", "default_value": True, "start_version": 830},
}


class ThematicTrimmingManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> ThematicTrimmingFormFields:
        """
        Get Thematic Trimming field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        study_ver = file_study.config.version
        config = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        trimming_config = config.get("variables selection", None)
        selected_vars_reset = (
            trimming_config.get("selected_vars_reset", True)
            if trimming_config
            else None
        )

        def get_value(field_info: FieldInfo) -> Any:
            if study_ver < field_info.get("start_version", -1):  # type: ignore
                return None

            if selected_vars_reset is None:
                return field_info["default_value"]

            var_name = field_info["path"]

            return (
                var_name not in trimming_config.get("select_var -", [])
                if selected_vars_reset
                else var_name in trimming_config.get("select_var +", [])
            )

        return ThematicTrimmingFormFields.construct(
            **{name: get_value(info) for name, info in FIELDS_INFO.items()}
        )

    def set_field_values(
        self, study: Study, field_values: ThematicTrimmingFormFields
    ) -> None:
        """
        Set Thematic Trimming config from the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        study_ver = file_study.config.version
        field_values_dict = field_values.dict()

        keys_by_bool: Dict[bool, List[Any]] = {True: [], False: []}
        for name, info in FIELDS_INFO.items():
            start_ver = info.get("start_version", 0)
            end_ver = info.get("end_version", study_ver)

            if start_ver <= study_ver <= end_ver:  # type: ignore
                keys_by_bool[field_values_dict[name]].append(info["path"])

        config_data: Dict[str, Any]
        if len(keys_by_bool[True]) > len(keys_by_bool[False]):
            config_data = {
                "selected_vars_reset": True,
                "select_var -": keys_by_bool[False],
            }
        else:
            config_data = {
                "selected_vars_reset": False,
                "select_var +": keys_by_bool[True],
            }

        execute_or_add_commands(
            study,
            file_study,
            [
                UpdateConfig(
                    target="settings/generaldata/variables selection",
                    data=config_data,
                    command_context=self.storage_service.variant_study_service.command_factory.command_context,
                )
            ],
            self.storage_service,
        )
