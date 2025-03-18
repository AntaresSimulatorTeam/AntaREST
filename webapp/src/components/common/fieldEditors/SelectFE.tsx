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
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  type SelectProps,
} from "@mui/material";
import { useMemo, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import * as RA from "ramda-adjunct";
import startCase from "lodash/startCase";
import type { O } from "ts-toolbelt";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";
import type { SvgIconComponent } from "@mui/icons-material";

type OptionObj<T extends O.Object = O.Object> = {
  label: string;
  value: string | number;
  icon?: SvgIconComponent;
} & T;

export interface SelectFEProps extends Omit<SelectProps, "labelId"> {
  options: Array<string | OptionObj> | readonly string[];
  helperText?: React.ReactNode;
  emptyValue?: boolean;
  startCaseLabel?: boolean;
}

function formatOptions(
  options: SelectFEProps["options"],
  startCaseLabel: boolean,
): Array<OptionObj<{ id: string }>> {
  return options.map((opt) => ({
    ...(RA.isPlainObj(opt) ? opt : { label: startCaseLabel ? startCase(opt) : opt, value: opt }),
    id: uuidv4(),
  }));
}

// TODO: replace with TextField with `select` prop https://mui.com/material-ui/react-text-field/#select

function SelectFE(props: SelectFEProps) {
  const {
    options,
    emptyValue,
    inputRef,
    variant,
    helperText,
    error,
    label,
    className,
    size,
    sx,
    fullWidth,
    startCaseLabel = true,
    ...selectProps
  } = props;

  const labelId = useRef(uuidv4()).current;

  const optionsFormatted = useMemo(
    () => formatOptions(options, startCaseLabel),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(options)],
  );

  return (
    <FormControl
      className={className}
      variant={variant}
      hiddenLabel={!label}
      error={error}
      sx={sx}
      fullWidth={fullWidth}
    >
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select {...selectProps} size={size} label={label} labelId={labelId}>
        {emptyValue && (
          <MenuItem value="">
            {/* TODO i18n */}
            <em>None</em>
          </MenuItem>
        )}
        {optionsFormatted.map(({ id, value, label, icon: Icon }) => (
          <MenuItem key={id} value={value}>
            {Icon && <Icon sx={{ mr: 1, verticalAlign: "sub" }} />}
            {label}
          </MenuItem>
        ))}
      </Select>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default reactHookFormSupport<SelectFEProps["value"]>({
  defaultValue: (props: SelectFEProps) => (props.multiple ? [] : ""),
})(SelectFE);
