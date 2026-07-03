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
import { useDebouncedField } from "@/hooks/useDebouncedField";
import { Stack } from "@mui/material";
import * as R from "ramda";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import useOutput from "../../../-hooks/useOutput";
import useOutputFilters from "../../../-hooks/useOutputFilters";

function ResultFilters() {
  const output = useOutput();
  const { t } = useTranslation();
  const {
    monteCarloMode,
    setMonteCarloMode,
    year,
    setYear,
    dataType,
    setDataType,
    frequency,
    setFrequency,
  } = useOutputFilters();

  const { localValue: debouncedYear, handleChange: debouncedSetYear } = useDebouncedField({
    value: year,
    onChange: setYear,
    delay: 500,
    transformValue: (value: number) => R.clamp(1, output.nbYears, value),
  });

  useEffect(() => {
    if (monteCarloMode === "mc-all") {
      setYear(-1);
    } else if (monteCarloMode === "mc-ind" && year <= 0) {
      setYear(1);
    }
  }, [monteCarloMode, setYear, year]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Stack spacing={1}>
      <SelectFE
        label={t("study.outputs.monteCarlo")}
        value={monteCarloMode}
        options={[
          { value: "mc-all", label: "Synthesis" },
          { value: "mc-ind", label: "Year by year" },
          { value: "variable-per-variable", label: t("study.outputs.variablePerVariable") },
        ]}
        size="extra-small"
        sx={{ minWidth: 150 }}
        onChange={(event) => setMonteCarloMode(event.target.value)}
      />
      <SelectFE
        label={t("study.outputs.display")}
        value={dataType}
        options={[
          { value: "values", label: "General values" },
          { value: "details", label: "Thermal plants" },
          { value: "details-res", label: "Ren. clusters" },
          { value: "id", label: "RecordYears" },
          { value: "details-STstorage", label: "ST Storages" },
        ]}
        size="extra-small"
        sx={{ minWidth: 150 }}
        onChange={(event) => setDataType(event.target.value)}
      />
      <SelectFE
        label={t("study.outputs.temporality")}
        value={frequency}
        options={[
          { value: "hourly", label: "Hourly" },
          { value: "daily", label: "Daily" },
          { value: "weekly", label: "Weekly" },
          { value: "monthly", label: "Monthly" },
          { value: "annual", label: "Annual" },
        ]}
        size="extra-small"
        onChange={(event) => setFrequency(event.target.value)}
        sx={{ minWidth: 100 }}
      />
      {monteCarloMode === "mc-ind" && (
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
    </Stack>
  );
}

export default ResultFilters;
