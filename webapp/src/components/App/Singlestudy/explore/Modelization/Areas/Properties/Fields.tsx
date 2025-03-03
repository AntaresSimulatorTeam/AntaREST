/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import Fieldset from "../../../../../../common/Fieldset";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../common/Form";
import { ADEQUACY_PATCH_OPTIONS, type PropertiesFormFields } from "./utils";
import type { StudyMetadata } from "../../../../../../../types/types";

function Fields() {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<PropertiesFormFields>();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const studyVersion = Number(study.version);

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
      <Fieldset legend={t("study.modelization.properties.energyCost")}>
        <NumberFE
          name="energyCostUnsupplied"
          label={t("study.modelization.properties.unsupplied")}
          control={control}
        />
        <NumberFE
          name="energyCostSpilled"
          label={t("study.modelization.properties.spilled")}
          control={control}
        />
        <NumberFE
          name="spreadUnsuppliedEnergyCost"
          label={t("study.modelization.properties.spreadUnsupplied")}
          control={control}
        />
        <NumberFE
          name="spreadSpilledEnergyCost"
          label={t("study.modelization.properties.spreadSpilled")}
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.modelization.properties.lastResortShedding")}>
        <SwitchFE
          name="nonDispatchPower"
          label={t("study.modelization.properties.nonDispatchPower")}
          control={control}
        />
        <SwitchFE
          name="dispatchHydroPower"
          label={t("study.modelization.properties.dispatchHydroPower")}
          control={control}
        />
        <SwitchFE
          name="otherDispatchPower"
          label={t("study.modelization.properties.otherDispatchPower")}
          control={control}
        />
      </Fieldset>
      {studyVersion >= 830 && (
        <Fieldset legend="Adequacy patch">
          <SelectFE
            name="adequacyPatchMode"
            label={t("study.modelization.properties.adequacyPatch")}
            options={ADEQUACY_PATCH_OPTIONS}
            control={control}
            sx={{ minWidth: "200px" }}
          />
        </Fieldset>
      )}
      <Fieldset legend={t("study.modelization.properties.outputFilter")}>
        <SelectFE
          name="filterSynthesis"
          label={t("study.modelization.properties.filterSynthesis")}
          options={filterOptions}
          multiple
          control={control}
        />
        <SelectFE
          name="filterByYear"
          label={t("study.modelization.properties.filterByYear")}
          options={filterOptions}
          multiple
          control={control}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
