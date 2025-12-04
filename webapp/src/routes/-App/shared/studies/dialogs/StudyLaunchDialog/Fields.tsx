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

import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import { useFormContextPlus } from "@/components/Form";
import { validateNumber } from "@/utils/validation/number";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Box, IconButton, Tooltip } from "@mui/material";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  isXpressAvailableForVersion,
  otherOptionsToArray,
  XPRESS_OPTION,
  type FormValues,
} from "./utils";

function Fields() {
  const { control, setValue, setValues, getValues, watch } = useFormContextPlus<FormValues>();
  const { t } = useTranslation();

  const {
    isSingleStudy,
    outputOptions,
    launcherOptions,
    getVersionOptionsForLauncher,
    getConfigurationOptionsForVersion,
    solverPresetsById,
  } = getValues("_data") || {};

  const [configuration, isXpansionEnabled, isSensitivityModeEnabled, launcherId, version] = watch([
    "configuration",
    "xpansion",
    "sensitivityMode",
    "launcher",
    "version",
  ]);

  const versionOptions = useMemo(
    () => getVersionOptionsForLauncher?.(launcherId) || [],
    [getVersionOptionsForLauncher, launcherId],
  );

  const configurationOptions = useMemo(
    () => getConfigurationOptionsForVersion?.(version) || [],
    [getConfigurationOptionsForVersion, version],
  );

  const configurationTooltip = useMemo(() => {
    if (!configuration || !solverPresetsById?.[configuration]) {
      return null;
    }

    const { id, name, ...config } = solverPresetsById[configuration];

    return <pre>{JSON.stringify(config, null, 1)}</pre>;
  }, [configuration, solverPresetsById]);

  const isXpansionOutputEnabled = isXpansionEnabled && isSensitivityModeEnabled;

  // Ensure version is valid when launcher changes
  useEffect(() => {
    if (version && !versionOptions.includes(version)) {
      // We can set the version value with `versionOptions[0] || ""`,
      // but the user may not notice the change.
      setValue("version", "");
    }
  }, [setValue, version, versionOptions]);

  // Ensure configuration is valid when version changes
  useEffect(() => {
    if (configuration && !configurationOptions.find(({ value }) => value === configuration)) {
      setValue("configuration", configurationOptions[0]?.value || "");
    }
  }, [setValue, configuration, configurationOptions]);

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

  const validateAdequacyCriterion = (
    value: FormValues["adequacyCriterion"],
    { sensitivityMode }: FormValues,
  ) => {
    if (value && sensitivityMode) {
      return t("launcher.field.adequacyCriterion.error");
    }
    return true;
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleConfigurationChange = () => {
    setValue("otherOptions", "");
  };

  const handleXpansionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.checked) {
      setValues({
        adequacyCriterion: false,
        sensitivityMode: false,
        output: "",
      });
    }
  };

  const handleAdequacyCriterionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked && getValues("sensitivityMode")) {
      setValues({
        sensitivityMode: false,
        output: "",
      });
    }
  };

  const handleSensitivityModeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const isChecked = event.target.checked;

    if (isChecked && getValues("adequacyCriterion")) {
      setValue("adequacyCriterion", false);
    }

    if (!isChecked && getValues("output")) {
      setValue("output", "");
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
      <Fieldset>
        <StringFE label={t("global.name")} name="name" control={control} fullWidth />
        <SwitchFE
          label={t("launcher.field.autoUnzip")}
          name="autoUnzip"
          control={control}
          fullWidth
        />
        <SelectFE
          label={t("launcher.field.version")}
          name="version"
          options={versionOptions}
          control={control}
          rules={{ deps: ["otherOptions"] }}
          sx={{ flex: 1 / 3 }}
        />
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flex: 2 / 3 }}>
          <SelectFE
            label={t("launcher.field.configuration")}
            name="configuration"
            options={configurationOptions}
            emptyValue
            emptyValueLabel={t("launcher.field.otherOptions")}
            control={control}
            rules={{ deps: ["otherOptions"] }}
            onChange={handleConfigurationChange}
            sx={{ flex: 1 }}
          />
          {configurationTooltip && (
            <Tooltip title={configurationTooltip} placement="bottom-start">
              <IconButton>
                <InfoOutlinedIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        <StringFE
          label={t("launcher.field.otherOptions")}
          name="otherOptions"
          control={control}
          rules={{ validate: validateOtherOptions }}
          fullWidth
          disabled={!!configuration}
        />
      </Fieldset>

      <Fieldset
        legend={
          <SwitchFE
            label={t("launcher.legend.xpansion")}
            labelPlacement="start"
            name="xpansion"
            control={control}
            onChange={handleXpansionChange}
            sx={{ ".MuiFormControlLabel-root": { ml: 0 } }}
          />
        }
      >
        <>
          <SwitchFE
            label={t("launcher.field.adequacyCriterion")}
            name="adequacyCriterion"
            control={control}
            onChange={handleAdequacyCriterionChange}
            rules={{ validate: validateAdequacyCriterion }}
            fullWidth
            disabled={!isXpansionEnabled}
          />
          {isSingleStudy && (
            <>
              <SwitchFE
                label={t("launcher.field.sensitivityMode")}
                name="sensitivityMode"
                control={control}
                onChange={handleSensitivityModeChange}
                rules={{ deps: ["adequacyCriterion"] }}
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
          // "version" in deps allows to display an error in the `version` field
          // if there is no version options for the selected launcher
          rules={{ deps: ["version", "nbCores"] }}
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
