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

import { MenuItem, TextField, type TextFieldProps } from "@mui/material";
import { useTranslation } from "react-i18next";
import reactHookFormSupport from "../../../hoc/reactHookFormSupport";

interface BooleanFEChangeEvent {
  target: { value: boolean; name: string | undefined };
}

interface BooleanFEFocusEvent {
  target: { value: boolean; name: string | undefined };
}

export interface BooleanFEProps
  extends Omit<
    TextFieldProps,
    "value" | "defaultValue" | "select" | "type" | "children" | "onChange" | "onBlur" | "multiline"
  > {
  defaultValue?: boolean;
  value?: boolean;
  trueText?: string;
  falseText?: string;
  onChange?: (event: BooleanFEChangeEvent) => void;
  onBlur?: (event: BooleanFEFocusEvent) => void;
}

function BooleanFE({ trueText, falseText, onChange, onBlur, name, ...rest }: BooleanFEProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      const value = event.target.value === "true";
      onChange({ target: { value, name } });
    }
  };

  const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
    if (onBlur) {
      const value = event.target.value === "true";
      onBlur({ target: { value, name } });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TextField {...rest} name={name} onChange={handleChange} onBlur={handleBlur} select>
      <MenuItem value="true">{trueText || t("global.enable")}</MenuItem>
      <MenuItem value="false">{falseText || t("global.disable")}</MenuItem>
    </TextField>
  );
}

const BooleanFEWithRHF = reactHookFormSupport({ defaultValue: false })(BooleanFE);

export default BooleanFEWithRHF;
