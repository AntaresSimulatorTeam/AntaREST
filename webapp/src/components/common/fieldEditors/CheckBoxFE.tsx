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

import {
  Checkbox,
  CheckboxProps,
  FormControl,
  FormControlLabel,
  FormControlLabelProps,
  FormHelperText,
} from "@mui/material";

import reactHookFormSupport from "@/hoc/reactHookFormSupport";

export interface CheckBoxFEProps
  extends Omit<CheckboxProps, "checked" | "defaultChecked" | "defaultValue"> {
  value?: boolean;
  defaultValue?: boolean;
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

function CheckBoxFE(props: CheckBoxFEProps) {
  const {
    value,
    defaultValue,
    label,
    labelPlacement,
    helperText,
    error,
    className,
    sx,
    ...checkboxProps
  } = props;

  const fieldEditor = (
    <Checkbox
      {...checkboxProps}
      checked={value}
      defaultChecked={defaultValue}
    />
  );

  return (
    <FormControl className={className} sx={sx} error={error}>
      {label ? (
        <FormControlLabel
          control={fieldEditor}
          label={label}
          labelPlacement={labelPlacement}
        />
      ) : (
        fieldEditor
      )}
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default reactHookFormSupport({ defaultValue: false })(CheckBoxFE);
