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

import { mergeSxProp } from "@/utils/muiUtils";
import SearchIcon from "@mui/icons-material/Search";
import { InputAdornment, TextField, type TextFieldProps } from "@mui/material";
import clsx from "clsx";
import * as RA from "ramda-adjunct";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";

interface SearchFEProps
  extends Omit<TextFieldProps, "type" | "value" | "defaultValue" | "placeholder"> {
  value?: string;
  defaultValue?: string;
  onSearchValueChange?: (value: string) => void;
}

function SearchFE({
  onSearchValueChange,
  onChange,
  slotProps,
  className,
  sx,
  ...rest
}: SearchFEProps) {
  const { t } = useTranslation();
  const [isFieldFilled, setIsFieldFilled] = useState(
    RA.isString(rest.value) ? !!rest.value : !!rest.defaultValue,
  );

  useUpdateEffect(() => {
    setIsFieldFilled(!!rest.value);
  }, [rest.value]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange: TextFieldProps["onChange"] = (event) => {
    const newValue = event.target.value;
    onChange?.(event);
    onSearchValueChange?.(newValue);
    setIsFieldFilled(!!newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TextField
      {...rest}
      type="search"
      placeholder={t("global.search")}
      className={clsx("SearchFE", className)}
      sx={mergeSxProp(
        {
          minWidth: isFieldFilled ? 78 : 38,
          transition: "min-width 0.2s ease",
          ":focus-within": {
            minWidth: 150,
          },
        },
        sx,
      )}
      slotProps={{
        ...slotProps,
        input: {
          ...slotProps?.input,
          startAdornment: (
            <InputAdornment
              position="start"
              sx={{
                // Allow to focus the input when clicking on the icon
                pointerEvents: "none",
              }}
            >
              <SearchIcon />
            </InputAdornment>
          ),
        },
      }}
      onChange={handleChange}
    />
  );
}

export default SearchFE;
