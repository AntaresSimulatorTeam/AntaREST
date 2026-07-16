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

import CustomScrollbar from "@/components/CustomScrollbar";
import NumberFE from "@/components/fieldEditors/NumberFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import { useDebouncedField } from "@/hooks/useDebouncedField";
import { Stack } from "@mui/material";
import * as R from "ramda";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import useOutput from "../../../../-hooks/useOutput";
import useOutputFilters from "../../../../-hooks/useOutputFilters";
import VariablesFilters from "./VariablesFilters";
import { FREQUENCY_OPTIONS, getDataTypeOptions, MONTE_CARLO_MODE_OPTIONS } from "./utils";

function ResultFilters() {
  const output = useOutput();
  const { t } = useTranslation();
  const {
    item,
    monteCarloMode,
    setMonteCarloMode,
    year,
    setYear,
    dataType,
    setDataType,
    frequency,
    setFrequency,
  } = useOutputFilters();

  const isYearByYearMode = monteCarloMode === "mc-ind";

  const dataTypeOptions = useMemo(
    () => getDataTypeOptions(item, monteCarloMode),
    [item, monteCarloMode],
  );

  const { localValue: debouncedYear, handleChange: debouncedSetYear } = useDebouncedField({
    value: year,
    onChange: setYear,
    delay: 500,
    transformValue: (value: number) => R.clamp(1, output.nbYears, value),
  });

  // Reset year when 'Year by year' mode is toggled
  useEffect(() => {
    setYear(isYearByYearMode ? 1 : -1);
  }, [isYearByYearMode, setYear]);

  // Update dataType when options change if the current dataType is not in the new options
  useEffect(() => {
    if (!dataTypeOptions.some((option) => option.value === dataType)) {
      setDataType(dataTypeOptions[0].value);
    }
  }, [dataTypeOptions, dataType, setDataType]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <CustomScrollbar>
      <Stack spacing={1} sx={{ pt: 1 }}>
        <SelectFE
          label={t("study.outputs.monteCarlo")}
          value={monteCarloMode}
          options={MONTE_CARLO_MODE_OPTIONS}
          size="extra-small"
          sx={{ minWidth: 150 }}
          onChange={(event) => setMonteCarloMode(event.target.value)}
        />
        <SelectFE
          label={t("study.outputs.display")}
          value={dataType}
          options={dataTypeOptions}
          size="extra-small"
          sx={{ minWidth: 150 }}
          onChange={(event) => setDataType(event.target.value)}
        />
        <SelectFE
          label={t("study.outputs.temporality")}
          value={frequency}
          options={FREQUENCY_OPTIONS}
          size="extra-small"
          onChange={(event) => setFrequency(event.target.value)}
          sx={{ minWidth: 100 }}
        />
        {/* 'Year by year' mode */}
        {isYearByYearMode && (
          <NumberFE
            label={t("global.year")}
            value={debouncedYear}
            slotProps={{
              htmlInput: {
                min: 1,
                max: output.nbYears,
              },
            }}
            onChange={(event) => debouncedSetYear(Number(event.target.value))}
            size="extra-small"
            sx={{ width: 80 }}
          />
        )}
        {/* 'Variable per variable' mode */}
        {monteCarloMode === "variable-per-variable" && <VariablesFilters />}
      </Stack>
    </CustomScrollbar>
  );
}

export default ResultFilters;
