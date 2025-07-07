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
  type TextFieldProps,
} from "@mui/material";
import startCase from "lodash/startCase";
import * as RA from "ramda-adjunct";
import { useMemo } from "react";
import type { FieldPath, FieldValues } from "react-hook-form";
import { useTranslation } from "react-i18next";

type Value = string | number;

interface Option<T extends Value> {
  label: string;
  value: T;
  icon?: SvgIconComponent;
  tooltip?: string;
}

type Options<T extends Value> = Array<T | Option<T>>;

interface SingleSelect {
  multiple?: false;
  value?: Value;
  defaultValue?: Value;
  onSelectAllOptions?: never;
  onDeselectAllOptions?: never;
}

interface MultipleSelect<OptionValue extends Value = Value> {
  multiple: true;
  // `value` or `defaultValue` may differ from `options` at initialization.
  // Reason why `Value` is used instead of `OptionValue`.
  value?: Value[];
  defaultValue?: Value[];
  onSelectAllOptions?: (optionValues: OptionValue[]) => void;
  onDeselectAllOptions?: VoidFunction;
}

type NewSelectFEProps<OptionValue extends Value = Value> = {
  options?: Options<OptionValue>;
  emptyValue?: boolean;
  startCaseLabel?: boolean;
  renderValueAs?: "text" | "chip";
} & (SingleSelect | MultipleSelect<OptionValue>) &
  Omit<TextFieldProps, "select" | "type" | "value" | "defaultValue">;

function NewSelectFE<OptionValue extends Value = Value>({
  options = [],
  emptyValue = false,
  startCaseLabel = false,
  multiple = false,
  renderValueAs = "text",
  helperText,
  slotProps,
  onSelectAllOptions,
  onDeselectAllOptions,
  ...rest
}: NewSelectFEProps<OptionValue>) {
  const { t } = useTranslation();

  const optionsFormatted = useMemo(
    () =>
      options.map((opt) =>
        RA.isPlainObj(opt)
          ? opt
          : {
              label: startCaseLabel ? startCase(String(opt)) : String(opt),
              value: opt,
            },
      ),
    [options, startCaseLabel],
  );

  const hasOptionActions = multiple && (!!onSelectAllOptions || !!onDeselectAllOptions);

  ////////////////////////////////////////////////////////////////
  // Rendering
  ////////////////////////////////////////////////////////////////

  const renderSelectedValueAsChip = (value: unknown) => {
    return (
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
        {RA.ensureArray(value).map((v) => {
          const option = optionsFormatted.find((opt) => opt.value === v);
          return option ? (
            <Chip key={`${option.value}-${option.label}`} label={option.label} />
          ) : null;
        })}
      </Box>
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <TextField
        {...rest}
        select
        slotProps={{
          ...slotProps,
          select: {
            renderValue: renderValueAs === "chip" ? renderSelectedValueAsChip : undefined,
            multiple,
          },
        }}
        helperText={
          <>
            <Box>{helperText}</Box>
            {hasOptionActions && (
              <ButtonGroup variant="text" size="extra-small">
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
          </>
        }
      >
        {emptyValue && !multiple && (
          <MenuItem value="">
            <em>{t("global.none")}</em>
          </MenuItem>
        )}
        {optionsFormatted.map(({ value, label, icon: Icon, tooltip }) => (
          <MenuItem key={value + label} value={value}>
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
    </>
  );
}

const SelectFEWithRHFSupport = reactHookFormSupport<Value | Value[]>({
  defaultValue: (props: NewSelectFEProps) => (props.multiple ? [] : ""),
})(NewSelectFE);

// The HOC doesn't automatically forward component generics

export default SelectFEWithRHFSupport as <
  OptionValue extends Value = Value,
  TFieldValues extends FieldValues = FieldValues,
  TFieldName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  TContext = any,
>(
  props: ReactHookFormSupportProps<TFieldValues, TFieldName, TContext> &
    NewSelectFEProps<OptionValue>,
) => JSX.Element;
