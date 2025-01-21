/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { IconButton, InputAdornment } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import { useTranslation } from "react-i18next";
import clsx from "clsx";
import { useState } from "react";
import { useUpdateEffect } from "react-use";
import * as RA from "ramda-adjunct";
import StringFE, { type StringFEProps } from "./StringFE";

export interface SearchFE extends Omit<StringFEProps, "placeholder" | "label"> {
  InputProps?: Omit<StringFEProps["InputProps"], "startAdornment">;
  onSearchValueChange?: (value: string) => void;
  useLabel?: boolean;
  onClear?: VoidFunction;
}

function SearchFE(props: SearchFE) {
  const { onSearchValueChange, onChange, onClear, InputProps, useLabel, className, ...rest } =
    props;
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
      InputProps={{
        ...InputProps,
        startAdornment: (
          <InputAdornment position="start">
            <SearchIcon />
          </InputAdornment>
        ),
        endAdornment:
          onClear && isFieldFilled ? (
            <InputAdornment position="end">
              <IconButton onClick={onClear} edge="end">
                <ClearIcon />
              </IconButton>
            </InputAdornment>
          ) : null,
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
