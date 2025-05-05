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
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  type InputBaseProps,
  type SelectChangeEvent,
  type SxProps,
  type Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import type { GenericInfo } from "../../types/types";
import { mergeSxProp } from "../../utils/muiUtils";

interface Props {
  name: string;
  label?: string;
  list: GenericInfo[];
  data: string | undefined;
  setValue?: (data: string) => void;
  sx?: SxProps<Theme> | undefined;
  optional?: boolean;
  variant?: "filled" | "standard" | "outlined" | undefined;
  handleChange?: (key: string, value: string | number) => void;
  required?: boolean;
  disabled?: boolean;
  size?: InputBaseProps["size"];
}

function SelectSingle(props: Props) {
  const {
    name,
    label = name,
    list,
    data,
    setValue,
    sx,
    variant = "filled",
    optional,
    handleChange,
    required,
    disabled,
  } = props;
  const [t] = useTranslation();

  const basicHandleChange = (e: SelectChangeEvent<unknown>) => {
    if (setValue) {
      setValue(e.target.value as string);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormControl variant={variant} sx={mergeSxProp({ m: 0, width: 200 }, sx)} required={required}>
      <InputLabel id={`single-checkbox-label-${name}`}>{label}</InputLabel>
      <Select
        {...props}
        labelId={`single-checkbox-label-${name}`}
        id={`single-checkbox-${name}`}
        value={data}
        label={label}
        disabled={disabled}
        onChange={
          handleChange
            ? (e: SelectChangeEvent<unknown>) => handleChange(name, e.target.value as string)
            : basicHandleChange
        }
      >
        {optional && (
          <MenuItem key="None" value="">
            {t("global.none")}
          </MenuItem>
        )}
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            {t(name)}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export default SelectSingle;
