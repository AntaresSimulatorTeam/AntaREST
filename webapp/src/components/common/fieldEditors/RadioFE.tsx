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
  FormControl,
  FormControlLabel,
  FormControlLabelProps,
  FormHelperText,
  Radio,
  RadioProps,
} from "@mui/material";

export interface RadioFEProps extends RadioProps {
  label?: string;
  labelPlacement?: FormControlLabelProps["labelPlacement"];
  error?: boolean;
  helperText?: React.ReactNode;
}

function RadioFE(props: RadioFEProps) {
  const {
    value,
    label,
    labelPlacement,
    helperText,
    error,
    className,
    sx,
    ...radioProps
  } = props;

  const fieldEditor = <Radio value={value} {...radioProps} />;

  return (
    <FormControl className={className} sx={sx} error={error}>
      {label ? (
        <FormControlLabel
          control={fieldEditor}
          label={label}
          labelPlacement={labelPlacement}
          value={value} // For RadioGroup
        />
      ) : (
        fieldEditor
      )}
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
}

export default RadioFE;
