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

import reactHookFormSupport, { type ReactHookFormSupportProps } from "@/hoc/reactHookFormSupport";
import type { SvgIconComponent } from "@mui/icons-material";
import {
  Box,
  Button,
  ButtonGroup,
  Chip,
  MenuItem,
  TextField,
  Tooltip,
  Typography,
  type TextFieldProps,
} from "@mui/material";
// eslint-disable-next-line @typescript-eslint/no-restricted-imports
import type { SelectInputProps } from "@mui/material/Select/SelectInput";
import startCase from "lodash/startCase";
import * as RA from "ramda-adjunct";
import { useMemo, useState } from "react";
import type { FieldPath, FieldValues } from "react-hook-form";
import { useTranslation } from "react-i18next";

type AllowedValue = string | number;

interface Option<T extends AllowedValue> {
  label: string;
  value: T;
  icon?: SvgIconComponent;
  tooltip?: string;
}

type Options<T extends AllowedValue> = Array<T | Option<T>> | ReadonlyArray<T | Option<T>>;

// With the default event handler, the type of event depends on what caused the change
// (cf. SelectChangeEvent from MUI). This event type is used to ensure to have a consistent type
// for the `onChange` event handler.
export interface SelectFEChangeEvent<Value, EmptyValue extends boolean = false> {
  target: { value: EmptyValue extends true ? Value | "" : Value; name: string };
}

// `value` or `defaultValue` may differ from `options` at initialization.
// Reason why `AllowedValue` type is used for `value` and `defaultValue`
// instead of `OptionValue` type.

interface SingleSelect<OptionValue extends AllowedValue, EmptyValue extends boolean> {
  multiple?: false;
  value?: AllowedValue;
  defaultValue?: AllowedValue;
  emptyValue?: EmptyValue;
  onChange?: (event: SelectFEChangeEvent<OptionValue, EmptyValue>) => void;
  onSelectAllOptions?: never;
  onDeselectAllOptions?: never;
}

interface MultipleSelect<OptionValue extends AllowedValue, Value extends AllowedValue> {
  multiple: true;
  value?: Value[];
  defaultValue?: Value[];
  emptyValue?: never;
  onChange?: (event: SelectFEChangeEvent<Array<Value | OptionValue>>) => void;
  onSelectAllOptions?: (optionValues: OptionValue[]) => void;
  onDeselectAllOptions?: VoidFunction;
}

export type SelectFEProps<
  OptionValue extends AllowedValue = AllowedValue,
  Value extends AllowedValue = AllowedValue,
  EmptyValue extends boolean = false,
> = {
  options?: Options<OptionValue>;
  startCaseLabel?: boolean;
} & (SingleSelect<OptionValue, EmptyValue> | MultipleSelect<OptionValue, Value>) &
  Omit<
    TextFieldProps,
    "select" | "type" | "value" | "defaultValue" | "children" | "multiline" | "onChange"
  >;

function SelectFE<OptionValue extends AllowedValue = AllowedValue>({
  options = [],
  emptyValue = false,
  startCaseLabel = false,
  multiple = false,
  helperText,
  slotProps,
  onChange,
  onSelectAllOptions,
  onDeselectAllOptions,
  value,
  defaultValue,
  ...rest
}: SelectFEProps<OptionValue>) {
  const { t } = useTranslation();
  const [currentValue, setCurrentValue] = useState(value ?? defaultValue);

  const optionsFormatted = useMemo(
    () =>
      options.map((opt, index) =>
        RA.isPlainObj(opt)
          ? {
              ...opt,
              id: opt.value + opt.label + index,
            }
          : {
              label: startCaseLabel ? startCase(String(opt)) : String(opt),
              value: opt,
              id: String(opt) + index,
            },
      ),
    [options, startCaseLabel],
  );

  // Invalid options are values that are in the current value (multiple mode) but not in the options.
  // Add them to the options list is the only way to allow to remove them from the select input.
  const invalidOptions = useMemo(() => {
    if (!multiple || !Array.isArray(currentValue)) {
      return [];
    }

    const validValues: AllowedValue[] = optionsFormatted.map(({ value }) => value);

    return currentValue
      .filter((v) => !validValues.includes(v))
      .map((v, index) => ({ value: v, label: String(v), id: String(v) + index }));
  }, [currentValue, multiple, optionsFormatted]);

  const hasOptionActions = multiple && (!!onSelectAllOptions || !!onDeselectAllOptions);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getOptionByValue = (value: unknown) => {
    return optionsFormatted.find((opt) => opt.value === value);
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange: SelectInputProps["onChange"] = (event) => {
    const value = event.target.value as OptionValue & (AllowedValue[] | OptionValue[]);

    onChange?.({ target: { value, name: event.target.name } });

    setCurrentValue(value);
  };

  ////////////////////////////////////////////////////////////////
  // Rendering
  ////////////////////////////////////////////////////////////////

  const renderSelectedValueAsChip = (value: unknown) => {
    return (
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
        {RA.ensureArray(value).map((v, index) => {
          const option = getOptionByValue(v);

          return option ? (
            <Chip key={`${option.value}-${option.label}`} label={option.label} />
          ) : (
            <Chip key={index} label={String(v)} color="error" />
          );
        })}
      </Box>
    );
  };

  /**
   * Render the value as text, with a fallback for unknown values.
   * The default `renderValue` don't display the value if it is not in the options,
   * typically the initial value.
   *
   * @param value - The value to render.
   * @returns A string representation of the value.
   * If the value is not found in the options, it returns a representation with an error color.
   */
  const renderValueAsText = (value: unknown) => {
    const option = getOptionByValue(value);
    return option ? option.label : <Typography color="error">{String(value)}</Typography>;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TextField
      {...rest}
      value={value}
      defaultValue={defaultValue}
      select
      slotProps={{
        ...slotProps,
        select: {
          onChange: handleChange,
          renderValue: multiple ? renderSelectedValueAsChip : renderValueAsText,
          multiple,
        },
      }}
      helperText={
        helperText || hasOptionActions ? (
          <>
            {hasOptionActions && (
              <ButtonGroup variant="text" size="extra-small" sx={{ ml: "-14px" }}>
                {onSelectAllOptions && (
                  <Button
                    onClick={() => onSelectAllOptions(optionsFormatted.map(({ value }) => value))}
                  >
                    {t("button.selectAll")}
                  </Button>
                )}
                {onDeselectAllOptions && (
                  <Button onClick={onDeselectAllOptions}>{t("button.deselectAll")}</Button>
                )}
              </ButtonGroup>
            )}
            <Box>{helperText}</Box>
          </>
        ) : null
      }
    >
      {emptyValue && !multiple && (
        <MenuItem value="">
          <em>{t("global.none")}</em>
        </MenuItem>
      )}
      {invalidOptions.map(({ value, label, id }) => (
        <MenuItem key={id} value={value}>
          <Typography color="error">{label}</Typography>
        </MenuItem>
      ))}
      {optionsFormatted.map(({ value, label, icon: Icon, tooltip, id }) => (
        <MenuItem key={id} value={value}>
          {Icon && <Icon sx={{ mr: 1, verticalAlign: "sub" }} />}
          {tooltip ? (
            <Tooltip title={t(tooltip)} placement="right">
              <span>{label}</span>
            </Tooltip>
          ) : (
            label
          )}
        </MenuItem>
      ))}
    </TextField>
  );
}

const SelectFEWithRHF = reactHookFormSupport<AllowedValue | AllowedValue[]>({
  defaultValue: (props: SelectFEProps) => (props.multiple ? [] : ""),
})(SelectFE);

// The HOC doesn't automatically forward component generics

export default SelectFEWithRHF as <
  OptionValue extends AllowedValue = AllowedValue,
  Value extends AllowedValue = AllowedValue,
  EmptyValue extends boolean = false,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any,
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    SelectFEProps<OptionValue, Value, EmptyValue>,
) => JSX.Element;
