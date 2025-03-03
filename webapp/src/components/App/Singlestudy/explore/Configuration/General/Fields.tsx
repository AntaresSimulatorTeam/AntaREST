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

import { Box, Button, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import SettingsIcon from "@mui/icons-material/Settings";
import { useEffect } from "react";
import * as RA from "ramda-adjunct";
import type { Validate } from "react-hook-form";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import {
  BuildingMode,
  BUILDING_MODE_OPTIONS,
  FIRST_JANUARY_OPTIONS,
  MODE_OPTIONS,
  WEEK_OPTIONS,
  YEAR_OPTIONS,
  type GeneralFormFields,
  type SetDialogStateType,
} from "./utils";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import { useFormContextPlus } from "../../../../../common/Form";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import Fieldset from "../../../../../common/Fieldset";
import { FieldWithButton } from "./styles";

interface Props {
  setDialog: React.Dispatch<React.SetStateAction<SetDialogStateType>>;
}

function Fields(props: Props) {
  const { setDialog } = props;
  const [t] = useTranslation();
  const { control, setValue, watch } = useFormContextPlus<GeneralFormFields>();
  const [buildingMode, selectionMode, firstDay, lastDay, filtering, thematicTrimming] = watch([
    "buildingMode",
    "selectionMode",
    "firstDay",
    "lastDay",
    "filtering",
    "thematicTrimming",
  ]);

  // Only present on study versions < 710
  const hasFiltering = RA.isBoolean(filtering);

  useEffect(() => {
    if (buildingMode === BuildingMode.Derated) {
      setValue("nbYears", 1);
    }
  }, [buildingMode, setValue]);

  useEffect(
    () => {
      if (firstDay > 0 && firstDay <= 366 && firstDay > lastDay) {
        setValue("lastDay", firstDay);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [firstDay],
  );

  useEffect(
    () => {
      if (lastDay > 0 && lastDay <= 366 && lastDay < firstDay) {
        setValue("firstDay", lastDay);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [lastDay],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDayValidation: Validate<number, GeneralFormFields> = (value, formValues) => {
    if (value < 1 || Number.isNaN(value)) {
      return t("form.field.minValue", { 0: 1 });
    }
    if (formValues.firstDay > formValues.lastDay) {
      return false;
    }
    if (formValues.leapYear) {
      return value <= 366 ? true : t("study.configuration.general.day.error.leapYearMax");
    }
    return value <= 365 ? true : t("study.configuration.general.day.error.nonLeapYearMax");
  };

  const handleNbYearsValidation: Validate<number, GeneralFormFields> = (value, formValues) => {
    if (formValues.buildingMode === BuildingMode.Derated) {
      return value === 1 ? true : t("study.configuration.general.nbYears.error.derated");
    }
    if (value < 1) {
      return t("form.field.minValue", { 0: 1 });
    }
    return value <= 50000 ? true : t("form.field.maxValue", { 0: 50000 });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const thematicTrimmingButton = (
    <Button
      startIcon={<SettingsIcon />}
      onClick={() => setDialog("thematicTrimming")}
      disabled={!(hasFiltering ? filtering : thematicTrimming)}
    >
      {t("global.settings")}
    </Button>
  );

  return (
    <>
      <Fieldset legend={t("study.configuration.general.legend.simulation")}>
        <SelectFE
          name="mode"
          label={t("study.configuration.general.mode")}
          options={MODE_OPTIONS}
          control={control}
        />
        <NumberFE
          name="firstDay"
          label={t("study.configuration.general.firstDay")}
          control={control}
          rules={{
            deps: "lastDay",
            validate: handleDayValidation,
          }}
        />
        <NumberFE
          name="lastDay"
          label={t("study.configuration.general.lastDay")}
          control={control}
          rules={{
            deps: "firstDay",
            validate: handleDayValidation,
          }}
        />
      </Fieldset>
      <Fieldset legend={t("study.configuration.general.legend.calendar")}>
        <StringFE name="horizon" label="Horizon" control={control} />
        <SelectFE
          name="firstMonth"
          label={t("study.configuration.general.year")}
          options={YEAR_OPTIONS}
          control={control}
        />
        <SelectFE
          name="firstWeekDay"
          label={t("study.configuration.general.week")}
          options={WEEK_OPTIONS}
          control={control}
        />
        <SelectFE
          name="firstJanuary"
          label={t("study.configuration.general.firstDayOfYear")}
          options={FIRST_JANUARY_OPTIONS}
          control={control}
        />
        <SwitchFE
          name="leapYear"
          label={t("study.configuration.general.leapYear")}
          control={control}
          rules={{
            deps: ["firstDay", "lastDay"],
          }}
        />
      </Fieldset>
      <Box sx={{ display: "flex" }}>
        <Fieldset
          legend={t("study.configuration.general.legend.monteCarloScenarios")}
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <NumberFE
            name="nbYears"
            label={t("study.configuration.general.nbYears")}
            control={control}
            rules={{
              validate: handleNbYearsValidation,
            }}
          />
          <FieldWithButton>
            <SelectFE
              name="buildingMode"
              label={t("study.configuration.general.buildingMode")}
              options={BUILDING_MODE_OPTIONS}
              control={control}
              rules={{ deps: "nbYears" }}
            />
            <Button
              startIcon={<SettingsIcon />}
              onClick={() => setDialog("scenarioBuilder")}
              disabled={buildingMode !== BuildingMode.Custom}
            >
              {t("global.settings")}
            </Button>
          </FieldWithButton>
          <FieldWithButton>
            <BooleanFE
              name="selectionMode"
              label={t("study.configuration.general.selectionMode")}
              trueText="Custom"
              falseText="Automatic"
              control={control}
            />
            <Button
              startIcon={<SettingsIcon />}
              onClick={() => setDialog("scenarioPlaylist")}
              disabled={!selectionMode}
            >
              {t("global.settings")}
            </Button>
          </FieldWithButton>
        </Fieldset>
        <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />
        <Fieldset
          legend={t("study.configuration.general.legend.outputProfile")}
          sx={{
            flex: 1,
          }}
          contentProps={{
            sx: { flexDirection: "column" },
          }}
        >
          <SwitchFE
            name="simulationSynthesis"
            label={t("study.configuration.general.simulationSynthesis")}
            control={control}
          />
          <SwitchFE
            name="yearByYear"
            label={t("study.configuration.general.yearByYear")}
            control={control}
          />
          <SwitchFE
            name="mcScenario"
            label={t("study.configuration.general.mcScenario")}
            control={control}
          />
          {hasFiltering ? (
            <FieldWithButton>
              <SwitchFE
                name="filtering"
                label={t("study.configuration.general.filtering")}
                control={control}
              />
              {thematicTrimmingButton}
            </FieldWithButton>
          ) : (
            <>
              <BooleanFE
                name="geographicTrimming"
                label={t("study.configuration.general.geographicTrimming")}
                trueText="Custom"
                falseText="None"
                control={control}
              />
              <FieldWithButton>
                <BooleanFE
                  name="thematicTrimming"
                  label={t("study.configuration.general.thematicTrimming")}
                  trueText="Custom"
                  falseText="None"
                  control={control}
                />
                {thematicTrimmingButton}
              </FieldWithButton>
            </>
          )}
        </Fieldset>
      </Box>
    </>
  );
}

export default Fields;
