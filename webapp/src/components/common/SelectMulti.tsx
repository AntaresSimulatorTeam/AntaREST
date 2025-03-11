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

import {
  Box,
  Checkbox,
  Chip,
  FormControl,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  type SelectChangeEvent,
  type SxProps,
  type Theme,
} from "@mui/material";
import type { GenericInfo } from "../../types/types";
import { mergeSxProp } from "../../utils/muiUtils";

interface Props {
  name: string;
  list: GenericInfo[];
  data: string[];
  setValue: (data: string[]) => void;
  sx?: SxProps<Theme> | undefined;
  tagsMode?: boolean;
  required?: boolean;
}

function SelectMulti(props: Props) {
  const { name, list, data, setValue, tagsMode, sx, required } = props;

  const handleChange = (event: SelectChangeEvent<string[]>) => {
    const {
      target: { value },
    } = event;
    setValue(typeof value === "string" ? value.split(",") : value);
  };

  const chipRender = (selected: string[]): React.ReactNode => (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
      {selected.map((value) => {
        const element = list.find((item) =>
          typeof item.id === "string" ? item.id === value : item.id.toString() === value,
        );
        if (element) {
          return <Chip key={element.id} label={element.name} />;
        }
        return undefined;
      })}
    </Box>
  );

  const checkboxRender = (selected: string[]): string =>
    selected
      .map(
        (elm) =>
          list.find((item) =>
            typeof item.id === "string" ? item.id === elm : item.id.toString() === elm,
          )?.name,
      )
      .join(", ");

  return (
    <FormControl sx={mergeSxProp({ m: 1, width: 200 }, sx)} required={required}>
      <InputLabel id={`multiple-checkbox-label-${name}`}>{name}</InputLabel>
      <Select
        labelId={`multiple-checkbox-label-${name}`}
        id={`multiple-checkbox-${name}`}
        multiple
        value={data}
        onChange={handleChange}
        renderValue={tagsMode === true ? chipRender : checkboxRender}
      >
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            <Checkbox checked={data.indexOf(id as string) > -1} />
            <ListItemText primary={name} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export default SelectMulti;
