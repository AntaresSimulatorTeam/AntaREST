/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import i18n from "@/i18n";
import { isNumericValue } from "@/utils/numberUtils";
import { setValueAsNumber } from "@/utils/reactHookFormUtils";
import { TextField, type TextFieldProps } from "@mui/material";
import * as RA from "ramda-adjunct";

export interface NumberFEProps extends Omit<TextFieldProps, "type" | "value" | "defaultValue"> {
  value?: number;
  defaultValue?: number;
  onValueChange?: (value: number | null) => void;
}

function NumberFE({ onChange, onValueChange, ...rest }: NumberFEProps) {
  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange: NumberFEProps["onChange"] = (event) => {
    onChange?.(event);

    const value = event.target.value;
    onValueChange?.(isNumericValue(value) ? Number(value) : null);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TextField {...rest} onChange={handleChange} type="number" />;
}

const NumberFEWithRHF = reactHookFormSupport({
  defaultValue: "" as unknown as number,
  setValueAs: setValueAsNumber,
  preValidate: (value) => {
    return RA.isNumber(value) && !Number.isNaN(value) ? true : i18n.t("form.field.invalidValue");
  },
})(NumberFE);

export default NumberFEWithRHF;
