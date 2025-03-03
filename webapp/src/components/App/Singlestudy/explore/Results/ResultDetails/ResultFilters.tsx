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

import { Box, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import { DataType, matchesSearchTerm, Timestep } from "./utils";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import DownloadMatrixButton from "../../../../../common/buttons/DownloadMatrixButton";
import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import SearchFE from "@/components/common/fieldEditors/SearchFE";
import * as R from "ramda";
import { useState, useMemo, useEffect } from "react";
import FilterListOffIcon from "@mui/icons-material/FilterListOff";
import { useDebouncedField } from "@/hooks/useDebouncedField";

interface ColumnHeader {
  variable: string;
  unit: string;
  stat: string;
  original: string[];
}

interface Filters {
  search: string;
  exp: boolean;
  min: boolean;
  max: boolean;
  std: boolean;
  values: boolean;
}

const defaultFilters = {
  search: "",
  exp: true,
  min: true,
  max: true,
  std: true,
  values: true,
} as const;

interface Props {
  year: number;
  setYear: (year: number) => void;
  dataType: DataType;
  setDataType: (dataType: DataType) => void;
  timestep: Timestep;
  setTimestep: (timestep: Timestep) => void;
  maxYear: number;
  studyId: string;
  path: string;
  colHeaders: string[][];
  onColHeadersChange: (colHeaders: string[][], indices: number[]) => void;
}

function ResultFilters({
  year,
  setYear,
  dataType,
  setDataType,
  timestep,
  setTimestep,
  maxYear,
  studyId,
  path,
  colHeaders,
  onColHeadersChange,
}: Props) {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<Filters>(defaultFilters);

  const { localValue: localYear, handleChange: debouncedYearChange } = useDebouncedField({
    value: year,
    onChange: setYear,
    delay: 500,
    transformValue: (value: number) => R.clamp(1, maxYear, value),
  });

  const filtersApplied = useMemo(() => {
    return !R.equals(filters, defaultFilters);
  }, [filters]);

  const parsedHeaders = useMemo(() => {
    return colHeaders.map(
      (header): ColumnHeader => ({
        variable: String(header[0]).trim(),
        unit: String(header[1]).trim(),
        stat: String(header[2]).trim(),
        original: header,
      }),
    );
  }, [colHeaders]);

  // Process headers while keeping track of their original positions
  // This ensures we can properly filter the data matrix later
  // Example: if we filter out column 1, we need to know that column 2
  // becomes column 1 in the filtered view but maps to index 2 in the data
  const filteredHeaders = useMemo(() => {
    return parsedHeaders
      .map((header, index) => ({ ...header, index }))
      .filter((header) => {
        // Apply search filter
        if (filters.search) {
          const matchesVariable = matchesSearchTerm(header.variable, filters.search);

          const matchesUnit = matchesSearchTerm(header.unit, filters.search);

          if (!matchesVariable && !matchesUnit) {
            return false;
          }
        }

        // Apply statistical filters
        if (header.stat) {
          const stat = header.stat.toLowerCase();

          if (!filters.exp && stat.includes("exp")) {
            return false;
          }
          if (!filters.min && stat.includes("min")) {
            return false;
          }
          if (!filters.max && stat.includes("max")) {
            return false;
          }
          if (!filters.std && stat.includes("std")) {
            return false;
          }
          if (!filters.values && stat.includes("values")) {
            return false;
          }
        }

        return true;
      });
  }, [filters, parsedHeaders]);

  // Notify parent of both filtered headers and their original indices
  // This allows the parent to correctly map the filtered view back to the original data
  useEffect(() => {
    onColHeadersChange(
      filteredHeaders.map((h) => h.original),
      filteredHeaders.map((h) => h.index),
    );
  }, [filteredHeaders, onColHeadersChange]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleYearChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value);
    debouncedYearChange(value);
  };

  const handleSearchChange = (value: string) => {
    setFilters((prev) => ({ ...prev, search: value }));
  };

  const handleStatFilterChange = (stat: keyof Omit<Filters, "search">) => {
    setFilters((prev) => ({ ...prev, [stat]: !prev[stat] }));
  };

  const handleReset = () => {
    setFilters(defaultFilters);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  // Local filters (immediately applied on columns headers)
  const COLUMN_FILTERS = [
    {
      id: "search",
      label: "",
      field: (
        <Box sx={{ width: 200 }}>
          <SearchFE value={filters.search} onChange={(e) => handleSearchChange(e.target.value)} />
        </Box>
      ),
    },
    {
      id: "exp",
      label: "Exp",
      field: <CheckBoxFE value={filters.exp} onChange={() => handleStatFilterChange("exp")} />,
    },
    {
      id: "min",
      label: "Min",
      field: <CheckBoxFE value={filters.min} onChange={() => handleStatFilterChange("min")} />,
    },
    {
      id: "max",
      label: "Max",
      field: <CheckBoxFE value={filters.max} onChange={() => handleStatFilterChange("max")} />,
    },
    {
      id: "std",
      label: "Std",
      field: <CheckBoxFE value={filters.std} onChange={() => handleStatFilterChange("std")} />,
    },
    {
      id: "values",
      label: "Values",
      field: (
        <CheckBoxFE value={filters.values} onChange={() => handleStatFilterChange("values")} />
      ),
    },
    {
      id: "reset",
      label: "",
      field: (
        <IconButton color="primary" onClick={handleReset} disabled={!filtersApplied} sx={{ ml: 1 }}>
          <FilterListOffIcon />
        </IconButton>
      ),
    },
  ] as const;

  // Data filters (requiring API calls, refetch new result)
  const RESULT_FILTERS = [
    {
      label: `${t("study.results.mc")}:`,
      field: (
        <>
          <BooleanFE
            value={year <= 0}
            trueText="Synthesis"
            falseText="Year by year"
            variant="outlined"
            onChange={(event) => setYear(event?.target.value ? -1 : 1)}
          />
          {localYear > 0 && (
            <NumberFE
              variant="outlined"
              value={localYear}
              sx={{ m: 0, ml: 1, width: 80 }}
              inputProps={{
                min: 1,
                max: maxYear,
              }}
              onChange={handleYearChange}
            />
          )}
        </>
      ),
    },
    {
      label: `${t("study.results.display")}:`,
      field: (
        <SelectFE
          value={dataType}
          options={[
            { value: DataType.General, label: "General values" },
            { value: DataType.Thermal, label: "Thermal plants" },
            { value: DataType.Renewable, label: "Ren. clusters" },
            { value: DataType.Record, label: "RecordYears" },
            { value: DataType.STStorage, label: "ST Storages" },
          ]}
          variant="outlined"
          onChange={(event) => setDataType(event?.target.value as DataType)}
        />
      ),
    },
    {
      label: `${t("study.results.temporality")}:`,
      field: (
        <SelectFE
          value={timestep}
          options={[
            { value: Timestep.Hourly, label: "Hourly" },
            { value: Timestep.Daily, label: "Daily" },
            { value: Timestep.Weekly, label: "Weekly" },
            { value: Timestep.Monthly, label: "Monthly" },
            { value: Timestep.Annual, label: "Annual" },
          ]}
          variant="outlined"
          onChange={(event) => setTimestep(event?.target.value as Timestep)}
        />
      ),
    },
  ] as const;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        py: 1,
      }}
    >
      {/* Column Filters Group */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
        }}
      >
        {COLUMN_FILTERS.map(({ id, label, field }) => (
          <Box
            key={id}
            sx={{
              display: "flex",
              alignItems: "center",
            }}
          >
            <Box sx={{ opacity: 0.7 }}>{label}</Box>
            {field}
          </Box>
        ))}
      </Box>

      {/* Result Filters Group with Download Button */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
        }}
      >
        {RESULT_FILTERS.map(({ label, field }) => (
          <Box
            key={label}
            sx={{
              display: "flex",
              alignItems: "center",
              mr: 1,
            }}
          >
            <Box sx={{ opacity: 0.7, mr: 1 }}>{label}</Box>
            {field}
          </Box>
        ))}
        <DownloadMatrixButton studyId={studyId} path={path} />
      </Box>
    </Box>
  );
}

export default ResultFilters;
