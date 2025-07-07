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

import CheckBoxFE from "@/components/common/fieldEditors/CheckBoxFE";
import SearchFE from "@/components/common/fieldEditors/SearchFE";
import { useDebouncedField } from "@/hooks/useDebouncedField";
import FilterListIcon from "@mui/icons-material/FilterList";
import FilterListOffIcon from "@mui/icons-material/FilterListOff";
import { Box, IconButton, Tooltip } from "@mui/material";
import startCase from "lodash/startCase";
import * as R from "ramda";
import { Fragment, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import DownloadMatrixButton from "../../../../../common/buttons/DownloadMatrixButton";
import BooleanFE from "../../../../../common/fieldEditors/BooleanFE";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import { DataType, matchesSearchTerm, Timestep } from "./utils";
import CustomScrollbar from "@/components/common/CustomScrollbar";

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
  onToggleFilter: () => void;
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
  onToggleFilter,
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
      field: (
        <SearchFE
          value={filters.search}
          size="extra-small"
          onSearchValueChange={handleSearchChange}
          sx={{ maxWidth: 150 }}
        />
      ),
    },
    ...(["exp", "min", "max", "std", "values"] as const).map((col) => ({
      id: col,
      field: (
        <CheckBoxFE
          key={col}
          label={startCase(col)}
          labelPlacement="start"
          value={filters[col]}
          onChange={() => handleStatFilterChange(col)}
        />
      ),
    })),
    {
      id: "reset",
      field: (
        <IconButton sx={{ ml: 1 }} onClick={handleReset} disabled={!filtersApplied}>
          <FilterListOffIcon />
        </IconButton>
      ),
    },
  ] as const;

  // Data filters (requiring API calls, refetch new result)
  const RESULT_FILTERS = [
    {
      id: "mc",
      field: (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <BooleanFE
            label={t("study.results.mc")}
            value={year <= 0}
            trueText="Synthesis"
            falseText="Year by year"
            size="extra-small"
            margin="dense"
            onChange={(event) => setYear(event?.target.value ? -1 : 1)}
          />
          {localYear > 0 && (
            <NumberFE
              label={t("global.year")}
              size="extra-small"
              value={localYear}
              slotProps={{
                htmlInput: {
                  min: 1,
                  max: maxYear,
                },
              }}
              onChange={handleYearChange}
              margin="dense"
              sx={{ minWidth: 65 }}
            />
          )}
        </Box>
      ),
    },
    {
      id: "display",
      field: (
        <SelectFE
          label={t("study.results.display")}
          value={dataType}
          options={[
            { value: DataType.General, label: "General values" },
            { value: DataType.Thermal, label: "Thermal plants" },
            { value: DataType.Renewable, label: "Ren. clusters" },
            { value: DataType.Record, label: "RecordYears" },
            { value: DataType.STStorage, label: "ST Storages" },
          ]}
          size="extra-small"
          onChange={(event) => setDataType(event?.target.value as DataType)}
          margin="dense"
          sx={{ minWidth: 80 }}
        />
      ),
    },
    {
      id: "temporality",
      field: (
        <SelectFE
          label={t("study.results.temporality")}
          value={timestep}
          options={[
            { value: Timestep.Hourly, label: "Hourly" },
            { value: Timestep.Daily, label: "Daily" },
            { value: Timestep.Weekly, label: "Weekly" },
            { value: Timestep.Monthly, label: "Monthly" },
            { value: Timestep.Annual, label: "Annual" },
          ]}
          size="extra-small"
          onChange={(event) => setTimestep(event?.target.value as Timestep)}
          margin="dense"
          sx={{ minWidth: 93 }}
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
        flexDirection: "column",
        gap: 1,
        pb: 1,
      }}
    >
      <CustomScrollbar>
        <Box
          sx={{
            width: 1,
            display: "flex",
            alignItems: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              flex: 1,
            }}
          >
            {COLUMN_FILTERS.map(({ id, field }) => (
              <Fragment key={id}>{field}</Fragment>
            ))}
            {RESULT_FILTERS.map(({ id, field }) => (
              <Fragment key={id}>{field}</Fragment>
            ))}
          </Box>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Tooltip title={t("matrix.filter.filterData")}>
              <IconButton onClick={onToggleFilter}>
                <FilterListIcon />
              </IconButton>
            </Tooltip>
            <DownloadMatrixButton studyId={studyId} path={path} />
          </Box>
        </Box>
      </CustomScrollbar>
    </Box>
  );
}

export default ResultFilters;
