import React, { useState } from "react";
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
import { createDatesFromIndex } from "./utils";

interface PropTypes {
  matrix: MatrixType;
}

export default function MatrixGraphView(props: PropTypes) {
  const [t] = useTranslation();
  const { matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const [selectedColumns, setSelectedColumns] = useState<number[]>([]);
  const [monotonic, setMonotonic] = useState<boolean>(false);

  const handleChange = (event: SelectChangeEvent<Array<number>>) => {
    setSelectedColumns(event.target.value as number[]);
  };

  const monotonicChange = () => {
    setMonotonic(!monotonic);
  };

  const unitChange = (tabBase: Array<number>) => {
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
          <InputLabel id="chip-label">{t("data:graphSelector")}</InputLabel>
          <Select
            labelId="chip-label"
            id="matrix-chip"
            multiple
            value={selectedColumns}
            onChange={(
              event: SelectChangeEvent<Array<number>>,
              child: React.ReactNode
            ) => handleChange(event)}
            sx={{
              "& .MuiSelect-select": {
                pb: 1.5,
                minWidth: "100px",
              },
            }}
            input={
              <OutlinedInput id="select-chip" label={t("data:graphSelector")} />
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
          label={t("data:monotonicView")}
        />
      </Box>
      <Box display="block" width="100%" height="100%">
        <AutoSizer>
          {({ height, width }) => (
            <Plot
              data={selectedColumns.map((val) => ({
                x: monotonic
                  ? unitChange(index as Array<number>)
                  : createDatesFromIndex(index),
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
