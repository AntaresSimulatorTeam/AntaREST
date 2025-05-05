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

import { IconButton, InputAdornment, type SxProps, type Theme } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { useState } from "react";
import { useUpdateEffect } from "react-use";
import * as RA from "ramda-adjunct";
import StringFE, { type StringFEProps } from "./StringFE";
import { mergeSxProp } from "@/utils/muiUtils";

export interface SearchFE extends Omit<StringFEProps, "placeholder" | "label"> {
  onSearchValueChange?: (value: string) => void;
  useLabel?: boolean;
  onClear?: VoidFunction;
  sx?: SxProps<Theme>;
}

function SearchFE({
  onSearchValueChange,
  onChange,
  onClear,
  slotProps,
  useLabel,
  className,
  sx,
  ...rest
}: SearchFE) {
  const { t } = useTranslation();
  const placeholderOrLabel = {
    [useLabel ? "label" : "placeholder"]: t("global.search"),
  };

  const [isFieldFilled, setIsFieldFilled] = useState(
    RA.isString(rest.value) ? !!rest.value : !!rest.defaultValue,
  );

  useUpdateEffect(() => {
    setIsFieldFilled(!!rest.value);
  }, [rest.value]);

  return (
    <StringFE
      {...rest}
      {...placeholderOrLabel}
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
          endAdornment:
            onClear && isFieldFilled ? (
              <InputAdornment position="end">
                <IconButton onClick={() => onClear()} edge="end">
                  <ClearIcon />
                </IconButton>
              </InputAdornment>
            ) : null,
        },
      }}
      onChange={(event) => {
        const newValue = event.target.value;
        onChange?.(event);
        onSearchValueChange?.(newValue);
        setIsFieldFilled(!!newValue);
      }}
    />
  );
}

export default SearchFE;
