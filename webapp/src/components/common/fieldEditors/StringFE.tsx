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

import { Autocomplete, TextField, type TextFieldProps } from "@mui/material";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

// Used when a value is selected from the datalist
interface DatalistChangeEvent {
  target: { value: string; name: string };
}

type TextFieldChangeEvent = Parameters<NonNullable<TextFieldProps["onChange"]>>[0];

interface WithDatalist {
  datalist: string[] | readonly string[];
  onChange?: (event: DatalistChangeEvent | TextFieldChangeEvent) => void;
}

interface WithoutDatalist {
  datalist?: undefined;
  onChange?: TextFieldProps["onChange"];
}

export type StringFEProps = {
  value?: string;
  defaultValue?: string;
} & (WithDatalist | WithoutDatalist) &
  Omit<TextFieldProps, "type" | "value" | "defaultValue" | "onChange">;

function StringFE({ value, defaultValue, datalist, onChange, name, ...restProps }: StringFEProps) {
  const commonProps = {
    ...restProps,
    name,
    onChange,
    type: "text",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAutocompleteChange = (event: React.SyntheticEvent, value: string) => {
    if (datalist && onChange) {
      onChange({ target: { value: value, name: name || "" } });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (datalist) {
    return (
      <Autocomplete
        value={value}
        defaultValue={defaultValue}
        options={datalist}
        freeSolo
        disableClearable
        onChange={handleAutocompleteChange}
        renderInput={({ inputProps, InputProps, ...restParams }) => (
          <TextField
            {...restParams}
            {...commonProps}
            inputProps={inputProps}
            InputProps={InputProps}
          />
        )}
      />
    );
  }

  return <TextField value={value} defaultValue={defaultValue} {...commonProps} />;
}

const StringFEWithRHF = reactHookFormSupport({ defaultValue: "" })(StringFE);

export default StringFEWithRHF;
