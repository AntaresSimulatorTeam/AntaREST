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
import { Stack } from "@mui/material";
import * as R from "ramda";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useDebounce } from "react-use";
import useOutput from "../../../../-hooks/useOutput";
import useOutputContext from "../../../../-hooks/useOutputFilters";
import ColumnsFilters from "./ColumnsFilters";
import VariablesFilters from "./VariablesFilters";
import { FREQUENCY_OPTIONS, getDataTypeOptions, MONTE_CARLO_MODE_OPTIONS } from "./utils";

function ResultFilters() {
  const output = useOutput();
  const { t } = useTranslation();
  const {
    item,
    monteCarloMode,
    setMonteCarloMode,
    setYear,
    dataType,
    setDataType,
    frequency,
    setFrequency,
  } = useOutputContext();

  const [localYear, setLocalYear] = useState<number | null>(null);

  const isYearByYearMode = monteCarloMode === "mc-ind";
  const isVariablePerVariable = monteCarloMode === "variable-per-variable";

  const dataTypeOptions = useMemo(
    () => getDataTypeOptions(item, monteCarloMode),
    [item, monteCarloMode],
  );

  // Debounce updating the year to avoid frequent updates while typing
  useDebounce(
    () => {
      if (localYear !== null) {
        const v = R.clamp(1, output.nbYears, localYear);
        setYear(v);
        setLocalYear(v);
      }
    },
    500,
    [localYear],
  );

  // Reset year when 'Year by year' mode is toggled
  useEffect(() => {
    const v = isYearByYearMode ? 1 : -1;
    setYear(v);
    setLocalYear(v > 0 ? v : null);
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
      <Stack spacing={1} sx={{ pt: 1, width: "max-content" }}>
        {!isVariablePerVariable && <ColumnsFilters />}
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
            value={localYear ?? undefined}
            slotProps={{
              htmlInput: {
                min: 1,
                max: output.nbYears,
              },
            }}
            onValueChange={(value) => setLocalYear(value)}
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
