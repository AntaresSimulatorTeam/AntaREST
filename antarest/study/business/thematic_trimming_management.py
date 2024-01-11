import typing as t

from antarest.study.business.utils import (
    GENERAL_DATA_PATH,
    AllOptionalMetaclass,
    FieldInfo,
    FormFieldsBaseModel,
    execute_or_add_commands,
)
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig


class ThematicTrimmingFormFields(FormFieldsBaseModel, metaclass=AllOptionalMetaclass):
    """
    This class manages the configuration of result filtering in a simulation.

    This table allows the user to enable or disable specific variables before running a simulation.
    """

    ov_cost: bool
    op_cost: bool
    mrg_price: bool
    co2_emis: bool
    dtg_by_plant: bool
    balance: bool
    row_bal: bool
    psp: bool
    misc_ndg: bool
    load: bool
    h_ror: bool
    wind: bool
    solar: bool
    nuclear: bool
    lignite: bool
    coal: bool
    gas: bool
    oil: bool
    mix_fuel: bool
    misc_dtg: bool
    h_stor: bool
    h_pump: bool
    h_lev: bool
    h_infl: bool
    h_ovfl: bool
    h_val: bool
    h_cost: bool
    unsp_enrg: bool
    spil_enrg: bool
    lold: bool
    lolp: bool
    avl_dtg: bool
    dtg_mrg: bool
    max_mrg: bool
    np_cost: bool
    np_cost_by_plant: bool
    nodu: bool
    nodu_by_plant: bool
    flow_lin: bool
    ucap_lin: bool
    loop_flow: bool
    flow_quad: bool
    cong_fee_alg: bool
    cong_fee_abs: bool
    marg_cost: bool
    cong_prod_plus: bool
    cong_prod_minus: bool
    hurdle_cost: bool
    # For study versions >= 810
    res_generation_by_plant: bool
    misc_dtg_2: bool
    misc_dtg_3: bool
    misc_dtg_4: bool
    wind_offshore: bool
    wind_onshore: bool
    solar_concrt: bool
    solar_pv: bool
    solar_rooft: bool
    renw_1: bool
    renw_2: bool
    renw_3: bool
    renw_4: bool
    # For study versions >= 830
    dens: bool
    profit_by_plant: bool


FIELDS_INFO: t.Dict[str, FieldInfo] = {
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
    "cong_prod_plus": {"path": "CONG. PROB +", "default_value": True},
    "cong_prod_minus": {"path": "CONG. PROB -", "default_value": True},
    "hurdle_cost": {"path": "HURDLE COST", "default_value": True},
    "res_generation_by_plant": {"path": "RES generation by plant", "default_value": True, "start_version": 810},
    "misc_dtg_2": {"path": "MISC. DTG 2", "default_value": True, "start_version": 810},
    "misc_dtg_3": {"path": "MISC. DTG 3", "default_value": True, "start_version": 810},
    "misc_dtg_4": {"path": "MISC. DTG 4", "default_value": True, "start_version": 810},
    "wind_offshore": {"path": "WIND OFFSHORE", "default_value": True, "start_version": 810},
    "wind_onshore": {"path": "WIND ONSHORE", "default_value": True, "start_version": 810},
    "solar_concrt": {"path": "SOLAR CONCRT.", "default_value": True, "start_version": 810},
    "solar_pv": {"path": "SOLAR PV", "default_value": True, "start_version": 810},
    "solar_rooft": {"path": "SOLAR ROOFT", "default_value": True, "start_version": 810},
    "renw_1": {"path": "RENW. 1", "default_value": True, "start_version": 810},
    "renw_2": {"path": "RENW. 2", "default_value": True, "start_version": 810},
    "renw_3": {"path": "RENW. 3", "default_value": True, "start_version": 810},
    "renw_4": {"path": "RENW. 4", "default_value": True, "start_version": 810},
    "dens": {"path": "DENS", "default_value": True, "start_version": 830},
    "profit_by_plant": {"path": "Profit by plant", "default_value": True, "start_version": 830},
}


def get_fields_info(study_version: int) -> t.Mapping[str, FieldInfo]:
    return {key: info for key, info in FIELDS_INFO.items() if (info.get("start_version") or -1) <= study_version}


class ThematicTrimmingManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_field_values(self, study: Study) -> ThematicTrimmingFormFields:
        """
        Get Thematic Trimming field values for the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        config = file_study.tree.get(GENERAL_DATA_PATH.split("/"))
        trimming_config = config.get("variables selection") or {}
        exclude_vars = trimming_config.get("select_var -") or []
        include_vars = trimming_config.get("select_var +") or []
        selected_vars_reset = trimming_config.get("selected_vars_reset", True)

        def get_value(field_info: FieldInfo) -> t.Any:
            if selected_vars_reset is None:
                return field_info["default_value"]
            var_name = field_info["path"]
            return var_name not in exclude_vars if selected_vars_reset else var_name in include_vars

        fields_info = get_fields_info(int(study.version))
        fields_values = {name: get_value(info) for name, info in fields_info.items()}
        return ThematicTrimmingFormFields(**fields_values)

    def set_field_values(self, study: Study, field_values: ThematicTrimmingFormFields) -> None:
        """
        Set Thematic Trimming config from the webapp form
        """
        file_study = self.storage_service.get_storage(study).get_raw(study)
        field_values_dict = field_values.dict()

        keys_by_bool: t.Dict[bool, t.List[t.Any]] = {True: [], False: []}
        fields_info = get_fields_info(int(study.version))
        for name, info in fields_info.items():
            keys_by_bool[field_values_dict[name]].append(info["path"])

        config_data: t.Dict[str, t.Any]
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
