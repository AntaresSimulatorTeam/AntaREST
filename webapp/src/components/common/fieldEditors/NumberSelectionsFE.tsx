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
  label?: TextFieldProps["label"];
  maxNumber: number;
  onChange?: (numbers: number[] | null) => void;
  size?: TextFieldProps["size"];
  sx?: TextFieldProps["sx"];
}

function NumberSelectionsFE({ label, maxNumber, onChange, size, sx }: NumberSelectionsFEProps) {
  const [value, setValue] = useState("");
  const [selections, setSelections] = useState<NumberOrRange[] | null>([]);
  const { t } = useTranslation();

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
      setSelections(null);
      onChange?.(null);
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
    if (selections !== null) {
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
