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

import useFieldEditorValidation from "@/hooks/useFieldEditorValidation";
import {
  compactSelections,
  isSelectionsValid,
  selectionsToNumbers,
  selectionsToString,
  stringToSelections,
  type NumberOrRange,
} from "@/utils/numberSelectionsUtils";
import { TextField, Tooltip, type TextFieldProps } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

export interface NumberSelectionsFEProps {
  defaultValue?: NumberOrRange[];
  label?: TextFieldProps["label"];
  maxNumber: number;
  onChange?: (numbers: number[]) => void;
  size?: TextFieldProps["size"];
  sx?: TextFieldProps["sx"];
}

function NumberSelectionsFE({
  defaultValue = [],
  label,
  maxNumber,
  onChange,
  size,
  sx,
}: NumberSelectionsFEProps) {
  const { t } = useTranslation();
  const [selections, setSelections] = useState<NumberOrRange[]>(() =>
    compactSelections(defaultValue),
  );
  const [value, setValue] = useState(() => selectionsToString(selections));

  const {
    validateOnChange,
    validateOnBlur,
    validationState: { isValid, validationMessage },
  } = useFieldEditorValidation({
    customValidation: (event: React.ChangeEvent<HTMLInputElement>) => {
      if (!isSelectionsValid(event.target.value, maxNumber)) {
        return t("form.field.numberSelections.invalid");
      }
      return true;
    },
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value, validity } = event.target;

    setValue(value);

    if (!validity.valid) {
      setSelections([]);
      onChange?.([]);
      return;
    }

    const compactedSelections = compactSelections(stringToSelections(value));

    setSelections(compactedSelections);

    if (onChange) {
      onChange(selectionsToNumbers(compactedSelections));
    }
  };

  const handleBlur = () => {
    // Format current value with a consistent string representation
    if (selections.length > 0) {
      setValue(selectionsToString(selections));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip
      title={!isValid ? validationMessage : value.trim()}
      placement="top"
      disableFocusListener
    >
      <span>
        <TextField
          label={label}
          placeholder={t("form.field.numberSelections.help")}
          value={value}
          onChange={validateOnChange(handleChange)}
          onBlur={validateOnBlur(handleBlur)}
          size={size}
          error={!isValid}
          sx={sx}
        />
      </span>
    </Tooltip>
  );
}

export default NumberSelectionsFE;
