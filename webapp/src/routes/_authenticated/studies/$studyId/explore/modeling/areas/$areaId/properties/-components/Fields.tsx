/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { useMemo } from "react";
import { useFormContext } from "react-hook-form";
import { useTranslation } from "react-i18next";
import semver from "semver";
import { ADEQUACY_PATCH_OPTIONS, type PropertiesFormFields } from "../-utils";

function Fields() {
  const { t } = useTranslation();
  const { control } = useFormContext<PropertiesFormFields>();
  const study = useStudy();

  const filterOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly", "monthly", "annual"].map((filter) => ({
        label: t(`global.time.${filter}`),
        value: filter,
      })),
    [t],
  );

  return (
    <>
      <Fieldset legend={t("study.modeling.properties.energyCost")}>
        <NumberFE
          name="energyCostUnsupplied"
          label={t("study.modeling.properties.unsupplied")}
          control={control}
        />
        <NumberFE
          name="energyCostSpilled"
          label={t("study.modeling.properties.spilled")}
          control={control}
        />
        <NumberFE
          name="spreadUnsuppliedEnergyCost"
          label={t("study.modeling.properties.spreadUnsupplied")}
          control={control}
        />
        <NumberFE
          name="spreadSpilledEnergyCost"
          label={t("study.modeling.properties.spreadSpilled")}
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.modeling.properties.lastResortShedding")}>
        <SwitchFE
          name="nonDispatchPower"
          label={t("study.modeling.properties.nonDispatchPower")}
          control={control}
        />
        <SwitchFE
          name="dispatchHydroPower"
          label={t("study.modeling.properties.dispatchHydroPower")}
          control={control}
        />
        <SwitchFE
          name="otherDispatchPower"
          label={t("study.modeling.properties.otherDispatchPower")}
          control={control}
        />
      </Fieldset>
      {semver.gte(study.version, "8.3.0") && (
        <Fieldset legend="Adequacy patch">
          <SelectFE
            name="adequacyPatchMode"
            label={t("study.modeling.properties.adequacyPatch")}
            options={ADEQUACY_PATCH_OPTIONS}
            control={control}
            sx={{ minWidth: "200px" }}
          />
        </Fieldset>
      )}
      <Fieldset legend={t("study.modeling.properties.outputFilter")}>
        <SelectFE
          name="filterSynthesis"
          label={t("study.modeling.properties.filterSynthesis")}
          options={filterOptions}
          multiple
          control={control}
        />
        <SelectFE
          name="filterByYear"
          label={t("study.modeling.properties.filterByYear")}
          options={filterOptions}
          multiple
          control={control}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
