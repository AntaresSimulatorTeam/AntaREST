# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from antares.study.version import StudyVersion
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.core.serde import AntaresBaseModel
from antarest.study.model import (
    STUDY_VERSION_8_1,
    STUDY_VERSION_8_3,
    STUDY_VERSION_8_4,
    STUDY_VERSION_8_5,
    STUDY_VERSION_8_6,
    STUDY_VERSION_8_8,
    STUDY_VERSION_9_1,
    STUDY_VERSION_9_3,
)


class ThematicTrimming(AntaresBaseModel):
    """
    This class manages the configuration of result filtering in a simulation.

    This table allows the user to enable or disable specific variables before running a simulation.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    ov_cost: bool = True
    op_cost: bool = True
    mrg_price: bool = True
    co2_emis: bool = True
    dtg_by_plant: bool = True
    balance: bool = True
    row_bal: bool = True
    psp: bool = True
    misc_ndg: bool = True
    load: bool = True
    h_ror: bool = True
    wind: bool = True
    h_stor: bool = True
    h_pump: bool = True
    h_lev: bool = True
    h_infl: bool = True
    h_ovfl: bool = True
    h_val: bool = True
    h_cost: bool = True
    unsp_enrg: bool = True
    spil_enrg: bool = True
    lold: bool = True
    lolp: bool = True
    avl_dtg: bool = True
    dtg_mrg: bool = True
    max_mrg: bool = True
    np_cost: bool = True
    np_cost_by_plant: bool = True
    nodu: bool = True
    nodu_by_plant: bool = True
    flow_lin: bool = True
    ucap_lin: bool = True
    loop_flow: bool = True
    flow_quad: bool = True
    cong_fee_alg: bool = True
    cong_fee_abs: bool = True
    marg_cost: bool = True
    cong_prob_plus: bool = True
    cong_prob_minus: bool = True
    hurdle_cost: bool = True
    # Since v8.1
    res_generation_by_plant: bool | None = None
    # Since v8.3
    dens: bool | None = None
    profit_by_plant: bool | None = None
    # Since v8.4
    bc_marg_cost: bool | None = None
    # Since v8.5
    lmr_viol: bool | None = None
    dtg_mrg_csr: bool | None = None
    # Since v8.6
    sts_inj_by_plant: bool | None = None
    sts_withdrawal_by_plant: bool | None = None
    sts_lvl_by_plant: bool | None = None
    nh3_emis: bool | None = None
    nox_emis: bool | None = None
    pm2_5_emis: bool | None = None
    pm5_emis: bool | None = None
    pm10_emis: bool | None = None
    op1_emis: bool | None = None
    op2_emis: bool | None = None
    op3_emis: bool | None = None
    op4_emis: bool | None = None
    op5_emis: bool | None = None
    so2_emis: bool | None = None
    nmvoc_emis: bool | None = None
    # Since v8.8
    sts_cashflow_by_cluster: bool | None = None
    npcap_hours: bool | None = None
    # Since v9.1
    sts_by_group: bool | None = None
    # Since v9.3
    dispatch_gen: bool | None = None
    renewable_gen: bool | None = None
    # Introduced in v8.6 and removed in v9.1
    psp_open_injection: bool | None = None
    psp_open_withdrawal: bool | None = None
    psp_open_level: bool | None = None
    psp_closed_injection: bool | None = None
    psp_closed_withdrawal: bool | None = None
    psp_closed_level: bool | None = None
    pondage_injection: bool | None = None
    pondage_withdrawal: bool | None = None
    pondage_level: bool | None = None
    battery_injection: bool | None = None
    battery_withdrawal: bool | None = None
    battery_level: bool | None = None
    other1_injection: bool | None = None
    other1_withdrawal: bool | None = None
    other1_level: bool | None = None
    other2_injection: bool | None = None
    other2_withdrawal: bool | None = None
    other2_level: bool | None = None
    other3_injection: bool | None = None
    other3_withdrawal: bool | None = None
    other3_level: bool | None = None
    other4_injection: bool | None = None
    other4_withdrawal: bool | None = None
    other4_level: bool | None = None
    other5_injection: bool | None = None
    other5_withdrawal: bool | None = None
    other5_level: bool | None = None
    # Introduced in v8.1 and removed in v9.3
    misc_dtg_2: bool | None = None
    misc_dtg_3: bool | None = None
    misc_dtg_4: bool | None = None
    wind_offshore: bool | None = None
    wind_onshore: bool | None = None
    solar_concrt: bool | None = None
    solar_pv: bool | None = None
    solar_rooft: bool | None = None
    renw_1: bool | None = None
    renw_2: bool | None = None
    renw_3: bool | None = None
    renw_4: bool | None = None
    solar: bool | None = None
    nuclear: bool | None = None
    lignite: bool | None = None
    coal: bool | None = None
    gas: bool | None = None
    oil: bool | None = None
    mix_fuel: bool | None = None
    misc_dtg: bool | None = None


class ThematicTrimmingUpdate(AntaresBaseModel):
    """
    Represents an update of the thematic trimming.

    Only not-None fields will be used to update the thematic trimming.
    """

    model_config = ConfigDict(alias_generator=to_camel, extra="forbid", populate_by_name=True)

    ov_cost: bool | None = None
    op_cost: bool | None = None
    mrg_price: bool | None = None
    co2_emis: bool | None = None
    dtg_by_plant: bool | None = None
    balance: bool | None = None
    row_bal: bool | None = None
    psp: bool | None = None
    misc_ndg: bool | None = None
    load: bool | None = None
    h_ror: bool | None = None
    wind: bool | None = None
    solar: bool | None = None
    nuclear: bool | None = None
    lignite: bool | None = None
    coal: bool | None = None
    gas: bool | None = None
    oil: bool | None = None
    mix_fuel: bool | None = None
    misc_dtg: bool | None = None
    h_stor: bool | None = None
    h_pump: bool | None = None
    h_lev: bool | None = None
    h_infl: bool | None = None
    h_ovfl: bool | None = None
    h_val: bool | None = None
    h_cost: bool | None = None
    unsp_enrg: bool | None = None
    spil_enrg: bool | None = None
    lold: bool | None = None
    lolp: bool | None = None
    avl_dtg: bool | None = None
    dtg_mrg: bool | None = None
    max_mrg: bool | None = None
    np_cost: bool | None = None
    np_cost_by_plant: bool | None = None
    nodu: bool | None = None
    nodu_by_plant: bool | None = None
    flow_lin: bool | None = None
    ucap_lin: bool | None = None
    loop_flow: bool | None = None
    flow_quad: bool | None = None
    cong_fee_alg: bool | None = None
    cong_fee_abs: bool | None = None
    marg_cost: bool | None = None
    cong_prob_plus: bool | None = None
    cong_prob_minus: bool | None = None
    hurdle_cost: bool | None = None
    res_generation_by_plant: bool | None = None
    misc_dtg_2: bool | None = None
    misc_dtg_3: bool | None = None
    misc_dtg_4: bool | None = None
    wind_offshore: bool | None = None
    wind_onshore: bool | None = None
    solar_concrt: bool | None = None
    solar_pv: bool | None = None
    solar_rooft: bool | None = None
    renw_1: bool | None = None
    renw_2: bool | None = None
    renw_3: bool | None = None
    renw_4: bool | None = None
    dens: bool | None = None
    profit_by_plant: bool | None = None
    bc_marg_cost: bool | None = None
    sts_inj_by_plant: bool | None = None
    sts_withdrawal_by_plant: bool | None = None
    sts_lvl_by_plant: bool | None = None
    psp_open_injection: bool | None = None
    psp_open_withdrawal: bool | None = None
    psp_open_level: bool | None = None
    psp_closed_injection: bool | None = None
    psp_closed_withdrawal: bool | None = None
    psp_closed_level: bool | None = None
    pondage_injection: bool | None = None
    pondage_withdrawal: bool | None = None
    pondage_level: bool | None = None
    battery_injection: bool | None = None
    battery_withdrawal: bool | None = None
    battery_level: bool | None = None
    other1_injection: bool | None = None
    other1_withdrawal: bool | None = None
    other1_level: bool | None = None
    other2_injection: bool | None = None
    other2_withdrawal: bool | None = None
    other2_level: bool | None = None
    other3_injection: bool | None = None
    other3_withdrawal: bool | None = None
    other3_level: bool | None = None
    other4_injection: bool | None = None
    other4_withdrawal: bool | None = None
    other4_level: bool | None = None
    other5_injection: bool | None = None
    other5_withdrawal: bool | None = None
    other5_level: bool | None = None
    sts_cashflow_by_cluster: bool | None = None
    npcap_hours: bool | None = None
    sts_by_group: bool | None = None
    dispatch_gen: bool | None = None
    renewable_gen: bool | None = None
    lmr_viol: bool | None = None
    dtg_mrg_csr: bool | None = None
    nh3_emis: bool | None = None
    nox_emis: bool | None = None
    pm2_5_emis: bool | None = None
    pm5_emis: bool | None = None
    pm10_emis: bool | None = None
    op1_emis: bool | None = None
    op2_emis: bool | None = None
    op3_emis: bool | None = None
    op4_emis: bool | None = None
    op5_emis: bool | None = None
    so2_emis: bool | None = None
    nmvoc_emis: bool | None = None


def get_thematic_trimming_fields_according_to_version(version: StudyVersion) -> set[str]:
    fields = {
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
    }

    if version >= STUDY_VERSION_8_1:
        fields.update(
            [
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
        )

    if version >= STUDY_VERSION_8_3:
        fields.update(["dens", "profit_by_plant"])

    if version >= STUDY_VERSION_8_4:
        fields.add("bc_marg_cost")

    if version >= STUDY_VERSION_8_5:
        fields.update(["lmr_viol", "dtg_mrg_csr"])

    if version >= STUDY_VERSION_8_6:
        fields.update(
            [
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
                "nh3_emis",
                "nox_emis",
                "pm2_5_emis",
                "pm5_emis",
                "pm10_emis",
                "op1_emis",
                "op2_emis",
                "op3_emis",
                "op4_emis",
                "op5_emis",
                "so2_emis",
                "nmvoc_emis",
            ]
        )

    if version >= STUDY_VERSION_8_8:
        fields.update(["sts_cashflow_by_cluster", "npcap_hours"])

    if version >= STUDY_VERSION_9_1:
        fields.add("sts_by_group")
        for field in [
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
        ]:
            fields.remove(field)

    if version >= STUDY_VERSION_9_3:
        fields.update(["dispatch_gen", "renewable_gen"])
        for field in [
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
        ]:
            fields.remove(field)
    return fields


def _check_version(
    thematic_trimming: ThematicTrimming | ThematicTrimmingUpdate, field: str, version: StudyVersion
) -> None:
    if getattr(thematic_trimming, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_thematic_trimming_against_version(
    thematic_trimming: ThematicTrimming | ThematicTrimmingUpdate, version: StudyVersion
) -> None:
    forbidden_fields = set(
        thematic_trimming.__class__.model_fields
    ) - get_thematic_trimming_fields_according_to_version(version)
    for field in forbidden_fields:
        _check_version(thematic_trimming, field, version)


def initialize_thematic_trimming_against_version(thematic_trimming: ThematicTrimming, version: StudyVersion) -> None:
    validate_thematic_trimming_against_version(thematic_trimming, version)
    for field in get_thematic_trimming_fields_according_to_version(version):
        setattr(thematic_trimming, field, True)


def check_thematic_trimming_complete(thematic_trimming: ThematicTrimming, version: StudyVersion) -> None:
    """
    Raise ValueError if any version-relevant field on `thematic_trimming` is None.

    DAOs assume the caller hands them a fully populated object.
    """
    missing = [
        f for f in get_thematic_trimming_fields_according_to_version(version) if getattr(thematic_trimming, f) is None
    ]
    if missing:
        raise ValueError(f"Thematic trimming is missing required field(s) for version {version}: {missing}")


def update_thematic_trimming(trimming: ThematicTrimming, data: ThematicTrimmingUpdate) -> ThematicTrimming:
    """
    Updates the thematic trimming according to the provided update data.
    """
    return trimming.model_copy(update=data.model_dump(exclude_none=True))
