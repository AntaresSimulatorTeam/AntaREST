# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""
List of fields of the Thematic Trimming panel
"""

import math
from typing import Any, Mapping, Type, Union

from antares.study.version import StudyVersion

from antarest.study.business.all_optional_meta import all_optional_model
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.model import (
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_1,
)


@all_optional_model
class ThematicTrimmingFormFieldsBase(FormFieldsBaseModel):
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
    cong_prob_plus: bool
    cong_prob_minus: bool
    hurdle_cost: bool
    # since v8.1
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
    # since v8.3
    dens: bool
    profit_by_plant: bool


@all_optional_model
class ThematicTrimmingFormFields860(ThematicTrimmingFormFieldsBase):
    # topic: Short-Term Storages
    # since v8.6
    sts_inj_by_plant: bool
    sts_withdrawal_by_plant: bool
    sts_lvl_by_plant: bool
    sts_cashflow_by_cluster: bool
    # topic: Short-Term Storages - Group
    psp_open_injection: bool
    psp_open_withdrawal: bool
    psp_open_level: bool
    psp_closed_injection: bool
    psp_closed_withdrawal: bool
    psp_closed_level: bool
    pondage_injection: bool
    pondage_withdrawal: bool
    pondage_level: bool
    battery_injection: bool
    battery_withdrawal: bool
    battery_level: bool
    other1_injection: bool
    other1_withdrawal: bool
    other1_level: bool
    other2_injection: bool
    other2_withdrawal: bool
    other2_level: bool
    other3_injection: bool
    other3_withdrawal: bool
    other3_level: bool
    other4_injection: bool
    other4_withdrawal: bool
    other4_level: bool
    other5_injection: bool
    other5_withdrawal: bool
    other5_level: bool


@all_optional_model
class ThematicTrimmingFormFields910(ThematicTrimmingFormFieldsBase):
    sts_inj_by_plant: bool
    sts_withdrawal_by_plant: bool
    sts_lvl_by_plant: bool
    sts_cashflow_by_cluster: bool
    sts_by_group: bool


ThematicTrimmingFormFieldsType = Union[
    ThematicTrimmingFormFields910, ThematicTrimmingFormFields860, ThematicTrimmingFormFieldsBase
]


def get_thematic_trimming_cls(study_version: StudyVersion) -> Type[ThematicTrimmingFormFieldsType]:
    if study_version >= STUDY_VERSION_9_1:
        return ThematicTrimmingFormFields910
    elif study_version >= STUDY_VERSION_8_6:
        return ThematicTrimmingFormFields860
    else:
        return ThematicTrimmingFormFieldsBase


def create_thematic_trimming_config(study_version: StudyVersion, **kwargs: Any) -> ThematicTrimmingFormFieldsType:
    cls = get_thematic_trimming_cls(study_version)
    return cls.model_validate(kwargs)


_GENERAL = "General"
_SHORT_TERM_STORAGES = "Short-Term Storages"
_SHORT_TERM_STORAGES_GROUP = "Short-Term Storages - Group"

# fmt: off
FIELDS_INFO: Mapping[str, Mapping[str, Any]] = {
    "ov_cost": {"topic": _GENERAL, "path": "OV. COST", "default_value": True},
    "op_cost": {"topic": _GENERAL, "path": "OP. COST", "default_value": True},
    "mrg_price": {"topic": _GENERAL, "path": "MRG. PRICE", "default_value": True},
    "co2_emis": {"topic": _GENERAL, "path": "CO2 EMIS.", "default_value": True},
    "dtg_by_plant": {"topic": _GENERAL, "path": "DTG by plant", "default_value": True},
    "balance": {"topic": _GENERAL, "path": "BALANCE", "default_value": True},
    "row_bal": {"topic": _GENERAL, "path": "ROW BAL.", "default_value": True},
    "psp": {"topic": _GENERAL, "path": "PSP", "default_value": True},
    "misc_ndg": {"topic": _GENERAL, "path": "MISC. NDG", "default_value": True},
    "load": {"topic": _GENERAL, "path": "LOAD", "default_value": True},
    "h_ror": {"topic": _GENERAL, "path": "H. ROR", "default_value": True},
    "wind": {"topic": _GENERAL, "path": "WIND", "default_value": True},
    "solar": {"topic": _GENERAL, "path": "SOLAR", "default_value": True},
    "nuclear": {"topic": _GENERAL, "path": "NUCLEAR", "default_value": True},
    "lignite": {"topic": _GENERAL, "path": "LIGNITE", "default_value": True},
    "coal": {"topic": _GENERAL, "path": "COAL", "default_value": True},
    "gas": {"topic": _GENERAL, "path": "GAS", "default_value": True},
    "oil": {"topic": _GENERAL, "path": "OIL", "default_value": True},
    "mix_fuel": {"topic": _GENERAL, "path": "MIX. FUEL", "default_value": True},
    "misc_dtg": {"topic": _GENERAL, "path": "MISC. DTG", "default_value": True},
    "h_stor": {"topic": _GENERAL, "path": "H. STOR", "default_value": True},
    "h_pump": {"topic": _GENERAL, "path": "H. PUMP", "default_value": True},
    "h_lev": {"topic": _GENERAL, "path": "H. LEV", "default_value": True},
    "h_infl": {"topic": _GENERAL, "path": "H. INFL", "default_value": True},
    "h_ovfl": {"topic": _GENERAL, "path": "H. OVFL", "default_value": True},
    "h_val": {"topic": _GENERAL, "path": "H. VAL", "default_value": True},
    "h_cost": {"topic": _GENERAL, "path": "H. COST", "default_value": True},
    "unsp_enrg": {"topic": _GENERAL, "path": "UNSP. ENRG", "default_value": True},
    "spil_enrg": {"topic": _GENERAL, "path": "SPIL. ENRG", "default_value": True},
    "lold": {"topic": _GENERAL, "path": "LOLD", "default_value": True},
    "lolp": {"topic": _GENERAL, "path": "LOLP", "default_value": True},
    "avl_dtg": {"topic": _GENERAL, "path": "AVL DTG", "default_value": True},
    "dtg_mrg": {"topic": _GENERAL, "path": "DTG MRG", "default_value": True},
    "max_mrg": {"topic": _GENERAL, "path": "MAX MRG", "default_value": True},
    "np_cost": {"topic": _GENERAL, "path": "NP COST", "default_value": True},
    "np_cost_by_plant": {"topic": _GENERAL, "path": "NP Cost by plant", "default_value": True},
    "nodu": {"topic": _GENERAL, "path": "NODU", "default_value": True},
    "nodu_by_plant": {"topic": _GENERAL, "path": "NODU by plant", "default_value": True},
    "flow_lin": {"topic": _GENERAL, "path": "FLOW LIN.", "default_value": True},
    "ucap_lin": {"topic": _GENERAL, "path": "UCAP LIN.", "default_value": True},
    "loop_flow": {"topic": _GENERAL, "path": "LOOP FLOW", "default_value": True},
    "flow_quad": {"topic": _GENERAL, "path": "FLOW QUAD.", "default_value": True},
    "cong_fee_alg": {"topic": _GENERAL, "path": "CONG. FEE (ALG.)", "default_value": True},
    "cong_fee_abs": {"topic": _GENERAL, "path": "CONG. FEE (ABS.)", "default_value": True},
    "marg_cost": {"topic": _GENERAL, "path": "MARG. COST", "default_value": True},
    "cong_prob_plus": {"topic": _GENERAL, "path": "CONG. PROB +", "default_value": True},
    "cong_prob_minus": {"topic": _GENERAL, "path": "CONG. PROB -", "default_value": True},
    "hurdle_cost": {"topic": _GENERAL, "path": "HURDLE COST", "default_value": True},
    # since v8.1
    "res_generation_by_plant": {"topic": _GENERAL, "path": "RES generation by plant", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "misc_dtg_2": {"topic": _GENERAL, "path": "MISC. DTG 2", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "misc_dtg_3": {"topic": _GENERAL, "path": "MISC. DTG 3", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "misc_dtg_4": {"topic": _GENERAL, "path": "MISC. DTG 4", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "wind_offshore": {"topic": _GENERAL, "path": "WIND OFFSHORE", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "wind_onshore": {"topic": _GENERAL, "path": "WIND ONSHORE", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "solar_concrt": {"topic": _GENERAL, "path": "SOLAR CONCR", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "solar_pv": {"topic": _GENERAL, "path": "SOLAR PV", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "solar_rooft": {"topic": _GENERAL, "path": "SOLAR ROOFT", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "renw_1": {"topic": _GENERAL, "path": "RENW. 1", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "renw_2": {"topic": _GENERAL, "path": "RENW. 2", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "renw_3": {"topic": _GENERAL, "path": "RENW. 3", "default_value": True, "start_version": STUDY_VERSION_8_1},
    "renw_4": {"topic": _GENERAL, "path": "RENW. 4", "default_value": True, "start_version": STUDY_VERSION_8_1},
    # since v8.3
    "dens": {"topic": _GENERAL, "path": "DENS", "default_value": True, "start_version": STUDY_VERSION_8_3},
    "profit_by_plant": {"topic": _GENERAL, "path": "Profit by plant", "default_value": True, "start_version": STUDY_VERSION_8_3},
    # topic: "Short-Term Storages"
    # since v8.6
    "sts_inj_by_plant": {"topic": _SHORT_TERM_STORAGES, "path": "STS inj by plant", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "sts_withdrawal_by_plant": {"topic": _SHORT_TERM_STORAGES, "path": "STS withdrawal by plant", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "sts_lvl_by_plant": {"topic": _SHORT_TERM_STORAGES, "path": "STS lvl by plant", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "sts_cashflow_by_cluster": {"topic": _SHORT_TERM_STORAGES, "path": "STS Cashflow By Cluster", "default_value": True, "start_version": STUDY_VERSION_8_8},
    # topic: "Short-Term Storages - Group"
    "psp_open_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_open_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "psp_open_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_open_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "psp_open_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_open_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "psp_closed_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_closed_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "psp_closed_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_closed_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "psp_closed_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "PSP_closed_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "pondage_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Pondage_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "pondage_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Pondage_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "pondage_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Pondage_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "battery_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Battery_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "battery_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Battery_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "battery_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Battery_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other1_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other1_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other1_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other1_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other1_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other1_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other2_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other2_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other2_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other2_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other2_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other2_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other3_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other3_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other3_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other3_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other3_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other3_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other4_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other4_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other4_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other4_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other4_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other4_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other5_injection": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other5_injection", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other5_withdrawal": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other5_withdrawal", "default_value": True, "start_version": STUDY_VERSION_8_6},
    "other5_level": {"topic": _SHORT_TERM_STORAGES_GROUP, "path": "Other5_level", "default_value": True, "start_version": STUDY_VERSION_8_6},
}
# fmt: on


def get_fields_info(study_version: StudyVersion) -> Mapping[str, Mapping[str, Any]]:
    highest_version = StudyVersion.parse(math.inf)
    lowest_version = StudyVersion.parse(0)
    return {
        key: info
        for key, info in FIELDS_INFO.items()
        if info.get("start_version", lowest_version) <= study_version
        and info.get("end_version", highest_version) > study_version
    }
