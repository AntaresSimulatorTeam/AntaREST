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
  Autocomplete,
  Checkbox,
  TextField,
  type AutocompleteProps,
  type AutocompleteValue,
} from "@mui/material";
import CheckBoxOutlineBlankIcon from "@mui/icons-material/CheckBoxOutlineBlank";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import type { FieldPath, FieldValues } from "react-hook-form";
import reactHookFormSupport, {
  type ReactHookFormSupportProps,
} from "../../../hoc/reactHookFormSupport";

interface CheckboxesTagsFEProps<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined,
> extends Omit<
    AutocompleteProps<T, true, DisableClearable, FreeSolo>,
    "multiple" | "disableCloseOnSelect" | "renderOption" | "renderInput" | "renderTags" | "onChange"
  > {
  label?: string;
  error?: boolean;
  helperText?: string;
  inputRef?: React.Ref<unknown>;
  name?: string;
  onChange?: (
    event: React.SyntheticEvent & {
      target: {
        value: AutocompleteValue<T, true, DisableClearable, FreeSolo>;
        name: string | "";
      };
    },
  ) => void;
}

// TODO Add `onChange`'s value in `inputRef` and `onBlur`'s event

function CheckboxesTagsFE<
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined,
>({
  label,
  // Default value on MUI
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getOptionLabel = (option: any) => option?.label ?? option,
  error,
  helperText,
  inputRef,
  onChange,
  name = "",
  ...rest
}: CheckboxesTagsFEProps<T, DisableClearable, FreeSolo>) {
  return (
    <Autocomplete
      {...rest}
      getOptionLabel={getOptionLabel}
      multiple
      disableCloseOnSelect
      onChange={(event, value) => {
        onChange?.({
          ...event,
          target: {
            ...event.target,
            value,
            name,
          },
        });
      }}
      renderOption={({ key, ...props }, option, { selected }) => (
        <li key={key} {...props}>
          <Checkbox
            size="extra-small"
            icon={<CheckBoxOutlineBlankIcon />}
            checkedIcon={<CheckBoxIcon />}
            style={{ marginRight: 8 }}
            checked={selected}
          />
          {getOptionLabel(option)}
        </li>
      )}
      renderInput={(params) => (
        <TextField
          name={name}
          label={label}
          error={error}
          helperText={helperText}
          inputRef={inputRef}
          {...params}
        />
      )}
    />
  );
}

// TODO find a clean solution to support generics

export default reactHookFormSupport()(CheckboxesTagsFE) as <
  T,
  DisableClearable extends boolean | undefined = undefined,
  FreeSolo extends boolean | undefined = undefined,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any,
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    CheckboxesTagsFEProps<T, DisableClearable, FreeSolo>,
) => JSX.Element;
