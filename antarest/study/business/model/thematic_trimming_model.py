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

from typing import Optional

from antares.study.version import StudyVersion

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.utils import FormFieldsBaseModel
from antarest.study.model import (
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_1,
    STUDY_VERSION_9_3,
)


class ThematicTrimming(FormFieldsBaseModel):
    """
    This class manages the configuration of result filtering in a simulation.

    This table allows the user to enable or disable specific variables before running a simulation.
    """

    ov_cost: Optional[bool] = None
    op_cost: Optional[bool] = None
    mrg_price: Optional[bool] = None
    co2_emis: Optional[bool] = None
    dtg_by_plant: Optional[bool] = None
    balance: Optional[bool] = None
    row_bal: Optional[bool] = None
    psp: Optional[bool] = None
    misc_ndg: Optional[bool] = None
    load: Optional[bool] = None
    h_ror: Optional[bool] = None
    wind: Optional[bool] = None
    solar: Optional[bool] = None
    nuclear: Optional[bool] = None
    lignite: Optional[bool] = None
    coal: Optional[bool] = None
    gas: Optional[bool] = None
    oil: Optional[bool] = None
    mix_fuel: Optional[bool] = None
    misc_dtg: Optional[bool] = None
    h_stor: Optional[bool] = None
    h_pump: Optional[bool] = None
    h_lev: Optional[bool] = None
    h_infl: Optional[bool] = None
    h_ovfl: Optional[bool] = None
    h_val: Optional[bool] = None
    h_cost: Optional[bool] = None
    unsp_enrg: Optional[bool] = None
    spil_enrg: Optional[bool] = None
    lold: Optional[bool] = None
    lolp: Optional[bool] = None
    avl_dtg: Optional[bool] = None
    dtg_mrg: Optional[bool] = None
    max_mrg: Optional[bool] = None
    np_cost: Optional[bool] = None
    np_cost_by_plant: Optional[bool] = None
    nodu: Optional[bool] = None
    nodu_by_plant: Optional[bool] = None
    flow_lin: Optional[bool] = None
    ucap_lin: Optional[bool] = None
    loop_flow: Optional[bool] = None
    flow_quad: Optional[bool] = None
    cong_fee_alg: Optional[bool] = None
    cong_fee_abs: Optional[bool] = None
    marg_cost: Optional[bool] = None
    cong_prob_plus: Optional[bool] = None
    cong_prob_minus: Optional[bool] = None
    hurdle_cost: Optional[bool] = None
    # since v8.1
    res_generation_by_plant: Optional[bool] = None
    misc_dtg_2: Optional[bool] = None
    misc_dtg_3: Optional[bool] = None
    misc_dtg_4: Optional[bool] = None
    wind_offshore: Optional[bool] = None
    wind_onshore: Optional[bool] = None
    solar_concrt: Optional[bool] = None
    solar_pv: Optional[bool] = None
    solar_rooft: Optional[bool] = None
    renw_1: Optional[bool] = None
    renw_2: Optional[bool] = None
    renw_3: Optional[bool] = None
    renw_4: Optional[bool] = None
    # since v8.3
    dens: Optional[bool] = None
    profit_by_plant: Optional[bool] = None
    # since v8.4
    bc_marg_cost: Optional[bool] = None
    # since v8.6
    sts_inj_by_plant: Optional[bool] = None
    sts_withdrawal_by_plant: Optional[bool] = None
    sts_lvl_by_plant: Optional[bool] = None
    psp_open_injection: Optional[bool] = None
    psp_open_withdrawal: Optional[bool] = None
    psp_open_level: Optional[bool] = None
    psp_closed_injection: Optional[bool] = None
    psp_closed_withdrawal: Optional[bool] = None
    psp_closed_level: Optional[bool] = None
    pondage_injection: Optional[bool] = None
    pondage_withdrawal: Optional[bool] = None
    pondage_level: Optional[bool] = None
    battery_injection: Optional[bool] = None
    battery_withdrawal: Optional[bool] = None
    battery_level: Optional[bool] = None
    other1_injection: Optional[bool] = None
    other1_withdrawal: Optional[bool] = None
    other1_level: Optional[bool] = None
    other2_injection: Optional[bool] = None
    other2_withdrawal: Optional[bool] = None
    other2_level: Optional[bool] = None
    other3_injection: Optional[bool] = None
    other3_withdrawal: Optional[bool] = None
    other3_level: Optional[bool] = None
    other4_injection: Optional[bool] = None
    other4_withdrawal: Optional[bool] = None
    other4_level: Optional[bool] = None
    other5_injection: Optional[bool] = None
    other5_withdrawal: Optional[bool] = None
    other5_level: Optional[bool] = None
    # Since v8.8
    sts_cashflow_by_cluster: Optional[bool] = None
    npcap_hours: Optional[bool] = None
    # Since v9.1
    sts_by_group: Optional[bool] = None
    # Since v9.3
    dispatch_gen: Optional[bool] = None
    renewable_gen: Optional[bool] = None


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
        "nuclear",
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


def _get_v_8_4_fields() -> list[str]:
    return ["bc_marg_cost"]


def _get_v_8_6_fields() -> list[str]:
    return [
        "sts_inj_by_plant",
        "sts_withdrawal_by_plant",
        "sts_lvl_by_plant",
        "psp_open_injection",
        "psp_open_withdrawal",
        "psp_open_level",
        "psp_closed_injection",
        "psp_closed_withdrawal",
        "psp_closed_level",
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


def _get_v_8_8_fields() -> list[str]:
    return ["sts_cashflow_by_cluster", "npcap_hours"]


def _get_v_9_1_fields() -> list[str]:
    return ["sts_by_group"]


def _get_v_9_3_fields() -> list[str]:
    return ["dispatch_gen", "renewable_gen"]


def _get_v_9_3_exclude_field() -> list[str]:
    return [
        # replaces by dispatch_gen
        "nuclear",
        "lignite",
        "coal",
        "gas",
        "oil",
        "mix_fuel",
        "misc_dtg",
        "misc_dtg_2",
        "misc_dtg_3",
        "misc_dtg_4",
        # replaced by renewable_gen
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


def _get_v_9_1_exclude_fields() -> list[str]:
    return [
        "psp_open_injection",
        "psp_open_withdrawal",
        "psp_open_level",
        "psp_closed_injection",
        "psp_closed_withdrawal",
        "psp_closed_level",
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


def _check_version(thematic_trimming: ThematicTrimming, field: str, version: StudyVersion) -> None:
    if getattr(thematic_trimming, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_against_version(thematic_trimming: ThematicTrimming, version: StudyVersion) -> None:
    if version < STUDY_VERSION_8_1:
        for field in _get_v_8_1_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_8_3:
        for field in _get_v_8_3_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_8_4:
        for field in _get_v_8_4_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_8_6:
        for field in _get_v_8_6_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_8_8:
        for field in _get_v_8_8_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_9_1:
        for field in _get_v_9_1_fields():
            _check_version(thematic_trimming, field, version)
    else:
        for field in _get_v_9_1_exclude_fields():
            _check_version(thematic_trimming, field, version)

    if version < STUDY_VERSION_9_3:
        for field in _get_v_9_3_fields():
            _check_version(thematic_trimming, field, version)
    else:
        for field in _get_v_9_3_exclude_field():
            _check_version(thematic_trimming, field, version)


def _initialize_field_default(thematic_trimming: ThematicTrimming, field: str, default_bool: bool) -> None:
    if getattr(thematic_trimming, field) is None:
        setattr(thematic_trimming, field, default_bool)


def _reset_field(thematic_trimming: ThematicTrimming, field: str) -> None:
    setattr(thematic_trimming, field, None)


def initialize_with_version(thematic_trimming: ThematicTrimming, version: StudyVersion, default_bool: bool) -> None:
    for field in _get_default_fields():
        _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_8_1:
        for field in _get_v_8_1_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_8_3:
        for field in _get_v_8_3_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_8_4:
        for field in _get_v_8_4_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_8_6:
        sts_fields = _get_v_8_6_fields()
        for field in sts_fields:
            _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_8_8:
        for field in _get_v_8_8_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)

    if version >= STUDY_VERSION_9_1:
        for field in _get_v_9_1_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)
        for field in _get_v_9_1_exclude_fields():
            _reset_field(thematic_trimming, field)

    if version >= STUDY_VERSION_9_3:
        for field in _get_v_9_3_fields():
            _initialize_field_default(thematic_trimming, field, default_bool)
        for field in _get_v_9_3_exclude_field():
            _reset_field(thematic_trimming, field)
