from typing import Any, Self, TypeAlias

from antares.study.version import StudyVersion
from pydantic import Field

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.thematic_trimming_model import ThematicTrimming
from antarest.study.model import (
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_1,
)


class ThematicTrimmingFileData(AntaresBaseModel, populate_by_name=True):
    """
    This class manages the configuration of result filtering in a simulation.

    This table allows the user to enable or disable specific variables before running a simulation.
    """

    ov_cost: bool | None = Field(default=None, alias="OV. COST")
    op_cost: bool | None = Field(default=None, alias="OP. COST")
    mrg_price: bool | None = Field(default=None, alias="MRG. PRICE")
    co2_emis: bool | None = Field(default=None, alias="CO2 EMIS.")
    dtg_by_plant: bool | None = Field(default=None, alias="DTG by plant")
    balance: bool | None = Field(default=None, alias="BALANCE")
    row_bal: bool | None = Field(default=None, alias="ROW BAL.")
    psp: bool | None = Field(default=None, alias="PSP")
    misc_ndg: bool | None = Field(default=None, alias="MISC. NDG")
    load: bool | None = Field(default=None, alias="LOAD")
    h_ror: bool | None = Field(default=None, alias="H. ROR")
    wind: bool | None = Field(default=None, alias="WIND")
    solar: bool | None = Field(default=None, alias="SOLAR")
    nuclear: bool | None = Field(default=None, alias="NUCLEAR")
    lignite: bool | None = Field(default=None, alias="LIGNITE")
    coal: bool | None = Field(default=None, alias="COAL")
    gas: bool | None = Field(default=None, alias="GAS")
    oil: bool | None = Field(default=None, alias="OIL")
    mix_fuel: bool | None = Field(default=None, alias="MIX. FUEL")
    misc_dtg: bool | None = Field(default=None, alias="MISC. DTG")
    h_stor: bool | None = Field(default=None, alias="H. STOR")
    h_pump: bool | None = Field(default=None, alias="H. PUMP")
    h_lev: bool | None = Field(default=None, alias="H. LEV")
    h_infl: bool | None = Field(default=None, alias="H. INFL")
    h_ovfl: bool | None = Field(default=None, alias="H. OVFL")
    h_val: bool | None = Field(default=None, alias="H. VAL")
    h_cost: bool | None = Field(default=None, alias="H. COST")
    unsp_enrg: bool | None = Field(default=None, alias="UNSP. ENRG")
    spil_enrg: bool | None = Field(default=None, alias="SPIL. ENRG")
    lold: bool | None = Field(default=None, alias="LOLD")
    lolp: bool | None = Field(default=None, alias="LOLP")
    avl_dtg: bool | None = Field(default=None, alias="AVL DTG")
    dtg_mrg: bool | None = Field(default=None, alias="DTG MRG")
    max_mrg: bool | None = Field(default=None, alias="MAX MRG")
    np_cost: bool | None = Field(default=None, alias="NP COST")
    np_cost_by_plant: bool | None = Field(default=None, alias="NP Cost by plant")
    nodu: bool | None = Field(default=None, alias="NODU")
    nodu_by_plant: bool | None = Field(default=None, alias="NODU by plant")
    flow_lin: bool | None = Field(default=None, alias="FLOW LIN.")
    ucap_lin: bool | None = Field(default=None, alias="UCAP LIN.")
    loop_flow: bool | None = Field(default=None, alias="LOOP FLOW")
    flow_quad: bool | None = Field(default=None, alias="FLOW QUAD.")
    cong_fee_alg: bool | None = Field(default=None, alias="CONG. FEE (ALG.)")
    cong_fee_abs: bool | None = Field(default=None, alias="CONG. FEE (ABS.)")
    marg_cost: bool | None = Field(default=None, alias="MARG. COST")
    cong_prob_plus: bool | None = Field(default=None, alias="CONG. PROB +")
    cong_prob_minus: bool | None = Field(default=None, alias="CONG. PROB -")
    hurdle_cost: bool | None = Field(default=None, alias="HURDLE COST")
    # since v8.1
    res_generation_by_plant: bool | None = Field(default=None, alias="RES generation by plant")
    misc_dtg_2: bool | None = Field(default=None, alias="MISC. DTG 2")
    misc_dtg_3: bool | None = Field(default=None, alias="MISC. DTG 3")
    misc_dtg_4: bool | None = Field(default=None, alias="MISC. DTG 4")
    wind_offshore: bool | None = Field(default=None, alias="WIND OFFSHORE")
    wind_onshore: bool | None = Field(default=None, alias="WIND ONSHORE")
    solar_concrt: bool | None = Field(default=None, alias="SOLAR CONCR")
    solar_pv: bool | None = Field(default=None, alias="SOLAR PV")
    solar_rooft: bool | None = Field(default=None, alias="SOLAR ROOFT")
    renw_1: bool | None = Field(default=None, alias="RENW. 1")
    renw_2: bool | None = Field(default=None, alias="RENW. 2")
    renw_3: bool | None = Field(default=None, alias="RENW. 3")
    renw_4: bool | None = Field(default=None, alias="RENW. 4")
    # since v8.3
    dens: bool | None = Field(default=None, alias="DENS")
    profit_by_plant: bool | None = Field(default=None, alias="Profit by plant")
    # since v8.6
    sts_inj_by_plant: bool | None = Field(default=None, alias="STS inj by plant")
    sts_withdrawal_by_plant: bool | None = Field(default=None, alias="STS withdrawal by plant")
    sts_lvl_by_plant: bool | None = Field(default=None, alias="STS lvl by plant")
    psp_open_injection: bool | None = Field(default=None, alias="PSP_open_injection")
    psp_open_withdrawal: bool | None = Field(default=None, alias="PSP_open_withdrawal")
    psp_open_level: bool | None = Field(default=None, alias="PSP_open_level")
    psp_closed_injection: bool | None = Field(default=None, alias="PSP_closed_injection")
    psp_closed_withdrawal: bool | None = Field(default=None, alias="PSP_closed_withdrawal")
    psp_closed_level: bool | None = Field(default=None, alias="PSP_closed_level")
    pondage_injection: bool | None = Field(default=None, alias="Pondage_injection")
    pondage_withdrawal: bool | None = Field(default=None, alias="Pondage_withdrawal")
    pondage_level: bool | None = Field(default=None, alias="Pondage_level")
    battery_injection: bool | None = Field(default=None, alias="Battery_injection")
    battery_withdrawal: bool | None = Field(default=None, alias="Battery_withdrawal")
    battery_level: bool | None = Field(default=None, alias="Battery_level")
    other1_injection: bool | None = Field(default=None, alias="Other1_injection")
    other1_withdrawal: bool | None = Field(default=None, alias="Other1_withdrawal")
    other1_level: bool | None = Field(default=None, alias="Other1_level")
    other2_injection: bool | None = Field(default=None, alias="Other2_injection")
    other2_withdrawal: bool | None = Field(default=None, alias="Other2_withdrawal")
    other2_level: bool | None = Field(default=None, alias="Other2_level")
    other3_injection: bool | None = Field(default=None, alias="Other3_injection")
    other3_withdrawal: bool | None = Field(default=None, alias="Other3_withdrawal")
    other3_level: bool | None = Field(default=None, alias="Other3_level")
    other4_injection: bool | None = Field(default=None, alias="Other4_injection")
    other4_withdrawal: bool | None = Field(default=None, alias="Other4_withdrawal")
    other4_level: bool | None = Field(default=None, alias="Other4_level")
    other5_injection: bool | None = Field(default=None, alias="Other5_injection")
    other5_withdrawal: bool | None = Field(default=None, alias="Other5_withdrawal")
    other5_level: bool | None = Field(default=None, alias="Other5_level")
    # Since v8.8
    sts_cashflow_by_cluster: bool | None = Field(default=None, alias="STS Cashflow By Cluster")
    # Since v9.1
    sts_by_group: bool | None = Field(default=None, alias="STS by group")

    def to_model(self) -> ThematicTrimming:
        return ThematicTrimming.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, thematic_trimming: ThematicTrimming) -> Self:
        return cls.model_validate(thematic_trimming.model_dump())

    @classmethod
    def parse_ini_file(cls, data: Any, study_version: StudyVersion) -> "ThematicTrimmingFileData":
        if data == {}:
            return ThematicTrimmingFileData()

        args = {}
        if data["selected_vars_reset"] is True:
            # Means written fields are deactivated and others are activated
            unselected_vars = data.get("select_var -", [])
            args = {var: False for var in unselected_vars}
            return ThematicTrimmingFileData(**args)

        # Means written fields are activated and others deactivated
        selected_vars = data.get("select_var +", [])
        args = {var: True for var in selected_vars}
        file_data = ThematicTrimmingFileData(**args)

        initialize_with_version(file_data, study_version, False)
        return file_data

    @classmethod
    def to_ini_file(cls, thematic_trimming: ThematicTrimming) -> dict[str, Any]:
        data = ThematicTrimmingFileData.from_model(thematic_trimming).model_dump(by_alias=True, exclude_none=True)
        content_plus = []
        content_minus = []
        for key, value in data.items():
            if value:
                content_plus.append(key)
            else:
                content_minus.append(key)
        if len(content_minus) >= len(cls.model_fields) // 2:
            ini_content: dict[str, Any] = {"selected_vars_reset": False}
            if content_plus:
                ini_content["select_var +"] = content_plus
        else:
            ini_content = {"selected_vars_reset": True}
            if content_minus:
                ini_content["select_var -"] = content_minus
        return ini_content


def parse_thematic_trimming(study_version: StudyVersion, data: Any) -> ThematicTrimming:
    thematic_trimming = ThematicTrimmingFileData.parse_ini_file(data, study_version).to_model()
    validate_against_version(thematic_trimming, study_version)
    initialize_with_version(thematic_trimming, study_version)
    return thematic_trimming


def serialize_thematic_trimming(study_version: StudyVersion, thematic_trimming: ThematicTrimming) -> dict[str, Any]:
    validate_against_version(thematic_trimming, study_version)
    return ThematicTrimmingFileData.to_ini_file(thematic_trimming)


def _get_default_fields() -> list[str]:
    return [
        "ov_cost",
        "op_cost",
        "mrg_price",
        "co2_emis",
        "dtg_by_plant",
        "balance",
        "row_bal",
        "psp",
        "misc_ndg",
        "load",
        "h_ror",
        "wind",
        "solar",
        "lignite",
        "coal",
        "gas",
        "oil",
        "mix_fuel",
        "misc_dtg",
        "h_stor",
        "h_pump",
        "h_lev",
        "h_infl",
        "h_ovfl",
        "h_val",
        "h_cost",
        "unsp_enrg",
        "spil_enrg",
        "lold",
        "lolp",
        "avl_dtg",
        "dtg_mrg",
        "max_mrg",
        "np_cost",
        "np_cost_by_plant",
        "nodu",
        "nodu_by_plant",
        "flow_lin",
        "ucap_lin",
        "loop_flow",
        "flow_quad",
        "cong_fee_alg",
        "cong_fee_abs",
        "marg_cost",
        "cong_prob_plus",
        "cong_prob_minus",
        "hurdle_cost",
    ]


def _get_v_8_1_fields() -> list[str]:
    return [
        "res_generation_by_plant",
        "misc_dtg_2",
        "misc_dtg_3",
        "misc_dtg_4",
        "wind_offshore",
        "wind_onshore",
        "solar_concrt",
        "solar_pv",
        "solar_rooft",
        "renw_1",
        "renw_2",
        "renw_3",
        "renw_4",
    ]


def _get_v_8_3_fields() -> list[str]:
    return ["dens", "profit_by_plant"]


def _get_v_8_8_fields() -> list[str]:
    return ["sts_cashflow_by_cluster"]


def _get_v_9_1_fields() -> list[str]:
    return ["sts_by_group"]


def _get_sts_fields() -> list[str]:
    return ["sts_inj_by_plant", "sts_withdrawal_by_plant", "sts_lvl_by_plant"]


def _get_sts_group_fields() -> list[str]:
    return [
        "psp_open_injection",
        "psp_open_withdrawal",
        "psp_open_level",
        "psp_closed_injection",
        "psp_closed_withdrawal",
        "pondage_injection",
        "pondage_withdrawal",
        "pondage_level",
        "battery_injection",
        "battery_withdrawal",
        "battery_level",
        "other1_injection",
        "other1_withdrawal",
        "other1_level",
        "other2_injection",
        "other2_withdrawal",
        "other2_level",
        "other3_injection",
        "other3_withdrawal",
        "other3_level",
        "other4_injection",
        "other4_withdrawal",
        "other4_level",
        "other5_injection",
        "other5_withdrawal",
        "other5_level",
    ]


ThematicTrimmingType: TypeAlias = ThematicTrimming | ThematicTrimmingFileData


def _check_version(trimming_object: ThematicTrimmingType, field: str, version: StudyVersion) -> None:
    if getattr(trimming_object, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_against_version(trimming_object: ThematicTrimmingType, version: StudyVersion) -> None:
    sts_group_fields = _get_sts_group_fields()

    if version < STUDY_VERSION_8_1:
        for field in _get_v_8_1_fields():
            _check_version(trimming_object, field, version)

    if version < STUDY_VERSION_8_3:
        for field in _get_v_8_3_fields():
            _check_version(trimming_object, field, version)

    if version < STUDY_VERSION_8_6:
        sts_fields = _get_sts_fields()
        sts_fields.extend(sts_group_fields)
        for field in sts_fields:
            _check_version(trimming_object, field, version)

    if version < STUDY_VERSION_8_8:
        for field in _get_v_8_8_fields():
            _check_version(trimming_object, field, version)

    if version < STUDY_VERSION_9_1:
        for field in _get_v_9_1_fields():
            _check_version(trimming_object, field, version)
    else:
        for field in sts_group_fields:
            _check_version(trimming_object, field, version)


def _initialize_field_default(trimming_object: ThematicTrimmingType, field: str, default_bool: bool) -> None:
    if getattr(trimming_object, field) is None:
        setattr(trimming_object, field, default_bool)


def initialize_with_version(
    trimming_object: ThematicTrimmingType, version: StudyVersion, default_bool: bool = True
) -> None:
    for field in _get_default_fields():
        _initialize_field_default(trimming_object, field, default_bool)

    if version >= STUDY_VERSION_8_1:
        for field in _get_v_8_1_fields():
            _initialize_field_default(trimming_object, field, default_bool)

    if version >= STUDY_VERSION_8_3:
        for field in _get_v_8_3_fields():
            _initialize_field_default(trimming_object, field, default_bool)

    if version >= STUDY_VERSION_8_6:
        sts_fields = _get_sts_fields()
        for field in sts_fields:
            _initialize_field_default(trimming_object, field, default_bool)
        if version < STUDY_VERSION_9_1:
            sts_group_fields = _get_sts_group_fields()
            for field in sts_group_fields:
                _initialize_field_default(trimming_object, field, default_bool)

    if version >= STUDY_VERSION_8_8:
        for field in _get_v_8_8_fields():
            _initialize_field_default(trimming_object, field, default_bool)

    if version >= STUDY_VERSION_9_1:
        for field in _get_v_9_1_fields():
            _initialize_field_default(trimming_object, field, default_bool)
