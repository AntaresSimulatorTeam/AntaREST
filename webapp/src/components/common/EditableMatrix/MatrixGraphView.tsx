/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useState } from "react";
import Plot from "react-plotly.js";
import AutoSizer from "react-virtualized-auto-sizer";
import {
  Box,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  InputLabel,
  MenuItem,
  OutlinedInput,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { MatrixType } from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import { formatDateFromIndex } from "./utils";

interface PropTypes {
  matrix: MatrixType;
}

export default function MatrixGraphView(props: PropTypes) {
  const [t] = useTranslation();
  const { matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const [selectedColumns, setSelectedColumns] = useState<number[]>([]);
  const [monotonic, setMonotonic] = useState<boolean>(false);

  const handleChange = (event: SelectChangeEvent<number[]>) => {
    setSelectedColumns(event.target.value as number[]);
  };

  const monotonicChange = () => {
    setMonotonic(!monotonic);
  };

  const unitChange = (tabBase: number[]) => {
    const stepLength = 100 / tabBase.length;
    return tabBase.map((el, i) => stepLength * (i + 1));
  };

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      alignItems="center"
    >
      <Box width="100%" display="flex" alignItems="center">
        <FormControl
          sx={{
            minWidth: "100px",
            my: 1,
          }}
        >
          <InputLabel id="chip-label">{t("matrix.graphSelector")}</InputLabel>
          <Select
            labelId="chip-label"
            id="matrix-chip"
            multiple
            value={selectedColumns}
            onChange={(
              event: SelectChangeEvent<number[]>,
              child: React.ReactNode,
            ) => handleChange(event)}
            sx={{
              "& .MuiSelect-select": {
                pb: 1.5,
                minWidth: "100px",
              },
            }}
            input={
              <OutlinedInput
                id="select-chip"
                label={t("matrix.graphSelector")}
              />
            }
            renderValue={(selected) => (
              <Box>
                {(selected as number[]).map((value) => (
                  <Chip
                    sx={{
                      mr: 1,
                      height: "24px",
                      "& span": {
                        padding: "8px",
                      },
                    }}
                    key={value}
                    label={columns[value]}
                  />
                ))}
              </Box>
            )}
          >
            {columns.map((column, i) => (
              <MenuItem key={column} value={i}>
                {column}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControlLabel
          sx={{ ml: 2 }}
          control={
            <Checkbox
              checked={monotonic}
              onChange={monotonicChange}
              name="checked"
              color="primary"
            />
          }
          label={t("matrix.monotonicView")}
        />
      </Box>
      <Box sx={{ display: "block", width: 1, height: 1, m: 1 }}>
        <AutoSizer>
          {({ height, width }) => (
            <Plot
              data={selectedColumns.map((val) => ({
                x: monotonic
                  ? unitChange(index as number[])
                  : formatDateFromIndex(index),
                y: monotonic
                  ? data.map((a) => a[val]).sort((b, c) => c - b)
                  : data.map((a) => a[val]),
                mode: "lines",
                name: `${columns[val]}`,
              }))}
              layout={{ width, height }}
            />
          )}
        </AutoSizer>
      </Box>
    </Box>
  );
}
