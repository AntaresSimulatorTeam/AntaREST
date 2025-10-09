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

import NumberFE from "@/components/common/fieldEditors/NumberFE";
import SelectFE, { type SelectFEChangeEvent } from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import Fieldset from "@/components/common/Fieldset";
import { useFormContextPlus } from "@/components/common/Form";
import { validateNumber } from "@/utils/validation/number";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import {
  isXpressAvailableForVersion,
  NULL_LAUNCHER,
  otherOptionsToArray,
  XPRESS_OPTION,
  type FormValues,
} from "./utils";

function Fields() {
  const { control, setValue, setValues, getValues, watch } = useFormContextPlus<FormValues>();
  const { t } = useTranslation();

  const { isSingleStudy, versionOptions, outputOptions, launcherOptions } =
    getValues("_data") || {};

  const [version, isXpansionEnabled, isSensitivityModeEnabled = NULL_LAUNCHER] = watch([
    "version",
    "xpansion",
    "sensitivityMode",
  ]);

  const isXpansionOutputEnabled = isXpansionEnabled && isSensitivityModeEnabled;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const updateOtherOptions = ({ xpress }: { xpress: boolean }) => {
    const currentOtherOptions = getValues("otherOptions");
    const options = otherOptionsToArray(currentOtherOptions);
    const hasXpress = options.includes(XPRESS_OPTION);

    if (xpress === hasXpress) {
      return;
    }

    const newOptions = xpress
      ? [...options, XPRESS_OPTION]
      : options.filter((opt) => opt !== XPRESS_OPTION);

    setValue("otherOptions", newOptions.join(" "));
  };

  ////////////////////////////////////////////////////////////////
  // Validations
  ////////////////////////////////////////////////////////////////

  const validateNbCores = (
    value: FormValues["nbCores"],
    { launcher, _data: { launchersById } }: FormValues,
  ) => {
    const currentLauncher = launchersById[launcher];

    return validateNumber(value, {
      min: currentLauncher.nbCores.min,
      max: currentLauncher.nbCores.max,
    });
  };

  const validateOtherOptions = (value: FormValues["otherOptions"], { version }: FormValues) => {
    const options = otherOptionsToArray(value);

    // Has duplicate options
    if (options.length !== new Set(options).size) {
      return t("launcher.field.otherOptions.error.duplicate");
    }

    // Xpress option not available for this version
    if (!isXpressAvailableForVersion(version) && options.includes(XPRESS_OPTION)) {
      return t("launcher.field.otherOptions.error.xpress");
    }

    return true;
  };

  const validateAdequacyCriterions = (
    value: FormValues["adequacyCriterions"],
    { sensitivityMode }: FormValues,
  ) => {
    if (value && sensitivityMode) {
      return t("launcher.field.adequacyCriterions.error");
    }
    return true;
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleVersionChange = (event: SelectFEChangeEvent<FormValues["version"]>) => {
    if (!isXpressAvailableForVersion(event.target.value) && getValues("xpress")) {
      setValue("xpress", false);
      updateOtherOptions({ xpress: false });
    }
  };

  const handleOtherOptionsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const otherOptions = otherOptionsToArray(event.target.value);
    const hasXpress = otherOptions.includes(XPRESS_OPTION);

    if (hasXpress !== getValues("xpress")) {
      setValue("xpress", hasXpress);
    }
  };

  const handleXpressChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    updateOtherOptions({ xpress: event.target.checked });
  };

  const handleAdequacyCriterionsChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked && getValues("sensitivityMode")) {
      setValue("sensitivityMode", false);
    }
  };

  const handleSensitivityModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked && getValues("adequacyCriterions")) {
      setValue("adequacyCriterions", false);
    }
  };

  const handleLauncherChange = (event: SelectFEChangeEvent<FormValues["launcher"]>) => {
    const launcherId = event.target.value;
    const launchersById = getValues("_data.launchersById");
    const newLauncher = launchersById[launcherId];

    setValues({
      nbCores: newLauncher.nbCores.default,
      timeLimit: newLauncher.timeLimit.default,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset fullFieldWidth>
        <StringFE label={t("global.name")} name="name" control={control} fullWidth />
      </Fieldset>

      <Fieldset legend={t("launcher.legend.simulator")}>
        <SelectFE
          label={t("global.version")}
          name="version"
          options={versionOptions}
          control={control}
          onChange={handleVersionChange}
          rules={{ deps: ["otherOptions"] }}
        />
        <StringFE
          label={t("launcher.field.otherOptions")}
          name="otherOptions"
          control={control}
          sx={{ flex: 1 }}
          onChange={handleOtherOptionsChange}
          rules={{ validate: validateOtherOptions }}
        />
        <Fieldset.Break />
        <SwitchFE
          label={t("launcher.field.xpress")}
          name="xpress"
          control={control}
          onChange={handleXpressChange}
          disabled={!isXpressAvailableForVersion(version)}
        />
        <SwitchFE
          label={t("launcher.field.autoUnzip")}
          name="autoUnzip"
          control={control}
          sx={{ flex: 1 }}
        />
      </Fieldset>

      <Fieldset
        legend={
          <Box sx={{ display: "flex", alignItems: "center" }}>
            {t("launcher.legend.xpansion")}
            <SwitchFE name="xpansion" control={control} />
          </Box>
        }
      >
        <>
          <SwitchFE
            label={t("launcher.field.adequacyCriterions")}
            name="adequacyCriterions"
            control={control}
            onChange={handleAdequacyCriterionsChange}
            rules={{ validate: validateAdequacyCriterions }}
            sx={{ minWidth: 250 }}
            disabled={!isXpansionEnabled}
          />
          {isSingleStudy && (
            <>
              <Fieldset.Break />
              <SwitchFE
                label={t("launcher.field.sensitivityMode")}
                name="sensitivityMode"
                control={control}
                onChange={handleSensitivityModeChange}
                rules={{ deps: ["adequacyCriterions"] }}
                disabled={!isXpansionEnabled}
              />

              <SelectFE
                label={t("global.output")}
                name="output"
                options={outputOptions}
                control={control}
                rules={{ required: isXpansionOutputEnabled ? t("form.field.required") : false }}
                sx={{ flex: 1 }}
                disabled={!isXpansionOutputEnabled}
              />
            </>
          )}
        </>
      </Fieldset>

      <Fieldset legend={t("launcher.legend.launcher")}>
        <SelectFE
          label={t("launcher.field.launcher")}
          name="launcher"
          options={launcherOptions}
          control={control}
          sx={{ flex: 1 }}
          onChange={handleLauncherChange}
          rules={{ deps: ["nbCores"] }}
        />
        <NumberFE
          label={t("launcher.field.nbCores")}
          name="nbCores"
          control={control}
          rules={{ validate: validateNbCores }}
        />
        {/* Field only to display the value, it is not editable */}
        <NumberFE
          label={t("launcher.field.timeLimit")}
          name="timeLimit"
          control={control}
          disabled
        />
      </Fieldset>
    </>
  );
}

export default Fields;
