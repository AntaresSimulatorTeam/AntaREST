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

  const [version, isXpansionEnabled, isSensitiveModeEnabled = NULL_LAUNCHER] = watch([
    "version",
    "xpansion",
    "sensitivityMode",
  ]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const updateOtherOptions = ({ xpress }: { xpress: boolean }) => {
    const currentOtherOptions = getValues("otherOptions");
    let options = otherOptionsToArray(currentOtherOptions);

    if (xpress) {
      if (!options.includes(XPRESS_OPTION)) {
        options.push(XPRESS_OPTION);
      }
    } else {
      options = options.filter((opt) => opt !== XPRESS_OPTION);
    }

    const newOtherOptions = options.join(" ");

    if (newOtherOptions !== currentOtherOptions) {
      setValue("otherOptions", newOtherOptions);
    }
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
        <SwitchFE label={t("launcher.field.autoUnzip")} name="autoUnzip" control={control} />
      </Fieldset>

      <Fieldset legend={t("launcher.legend.xpansion")}>
        <SwitchFE label={t("global.enable")} name="xpansion" control={control} />
        {isSingleStudy && (
          <>
            <SwitchFE
              label={t("launcher.field.sensitivityMode")}
              name="sensitivityMode"
              control={control}
              disabled={!isXpansionEnabled}
            />
            <SelectFE
              label={t("global.output")}
              name="output"
              options={outputOptions}
              control={control}
              disabled={!isXpansionEnabled || !isSensitiveModeEnabled}
              sx={{ flex: 1 }}
            />
          </>
        )}
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
