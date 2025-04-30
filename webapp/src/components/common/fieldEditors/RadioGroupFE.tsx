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

import reactHookFormSupport from "@/hoc/reactHookFormSupport";
import { mergeSxProp } from "@/utils/muiUtils";
import {
  FormControl,
  FormControlLabel,
  FormHelperText,
  FormLabel,
  Radio,
  RadioGroup,
  type FormControlLabelProps,
  type FormControlProps,
  type RadioGroupProps,
  type RadioProps,
} from "@mui/material";

export interface RadioGroupFEProps extends Omit<RadioGroupProps, "value" | "defaultValue"> {
  value?: string;
  defaultValue?: string;
  label?: React.ReactNode;
  radios?: Array<{
    value: string;
    label?: React.ReactNode;
    disabled?: boolean;
  }>;
  error?: boolean;
  helperText?: React.ReactNode;
  margin?: FormControlProps["margin"];
  size?: RadioProps["size"];
  fullWidth?: FormControlProps["fullWidth"];
  disabled?: boolean;
  inputRef?: FormControlLabelProps["inputRef"];
}

function RadioGroupFE({
  label,
  radios,
  helperText,
  error,
  className,
  sx,
  margin,
  size,
  fullWidth,
  disabled,
  inputRef,
  ...radioGroupProps
}: RadioGroupFEProps) {
  return (
    <FormControl
      className={className}
      sx={mergeSxProp({ pl: 1.5 }, sx)}
      error={error}
      margin={margin}
      fullWidth={fullWidth}
      disabled={disabled}
    >
      {label && <FormLabel>{label}</FormLabel>}
      <RadioGroup {...radioGroupProps}>
        {radios?.map(({ value, label, disabled }) => (
          <FormControlLabel
            key={value}
            value={value}
            control={<Radio size={size} />}
            label={label}
            disableTypography={typeof label === "string" ? false : true}
            disabled={disabled}
            inputRef={inputRef}
          />
        ))}
      </RadioGroup>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default reactHookFormSupport({ defaultValue: "" })(RadioGroupFE);
