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
  isSelectionsValid,
  selectionsToNumbers,
  selectionsToString,
  stringToSelections,
} from "@/utils/numberSelectionsUtils";
import { TextField, Tooltip, type TextFieldProps } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";

export interface NumberSelectionsFEProps {
  label?: TextFieldProps["label"];
  maxNumber: number;
  onChange?: (numbers: number[]) => void;
  size?: TextFieldProps["size"];
  sx?: TextFieldProps["sx"];
}

function NumberSelectionsFE({ label, maxNumber, onChange, size, sx }: NumberSelectionsFEProps) {
  const [selectionsValue, setSelectionsValue] = useState("");
  const [error, setError] = useState(false);
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectionsValue(event.target.value);
  };

  const handleBlur = () => {
    const isValid = isSelectionsValid(selectionsValue, maxNumber);

    setError(!isValid);

    if (!isValid) {
      onChange?.([]);
      return;
    }

    const selections = stringToSelections(selectionsValue);
    // If no selections, we return all numbers
    const numbers =
      selections.length === 0 ? R.range(1, maxNumber + 1) : selectionsToNumbers(selections);

    setSelectionsValue(selectionsToString(selections));
    onChange?.(numbers);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip
      title={error ? t("form.field.numberSelections.invalid") : selectionsValue.trim()}
      placement="top"
      disableFocusListener
    >
      <span>
        <TextField
          label={label}
          placeholder={t("form.field.numberSelections.help")}
          value={selectionsValue}
          onChange={handleChange}
          onBlur={handleBlur}
          size={size}
          error={error}
          sx={sx}
        />
      </span>
    </Tooltip>
  );
}

export default NumberSelectionsFE;
