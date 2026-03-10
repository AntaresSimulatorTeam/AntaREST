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

import CheckboxesTagsFE, {
  type CheckboxesTagsFEProps,
} from "@/components/fieldEditors/CheckboxesTagsFE";
import clsx from "clsx";
import { useTranslation } from "react-i18next";

interface SearchMultipleFEProps
  extends Omit<
    CheckboxesTagsFEProps<string, false, true>,
    "value" | "defaultValue" | "placeholder" | "options" | "freeSolo"
  > {
  value?: string[];
  defaultValue?: string[];
  onSearchValuesChange?: (values: string[]) => void;
  onInputValueChange?: (value: string) => void;
}

function SearchMultipleFE({
  onChange,
  onSearchValuesChange,
  onInputValueChange,
  className,
  ...rest
}: SearchMultipleFEProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange: SearchMultipleFEProps["onChange"] = (event) => {
    const newValue = event.target.value;
    onChange?.(event);
    onSearchValuesChange?.(newValue);
  };

  const handleInputChange: SearchMultipleFEProps["onInputChange"] = (_, value) => {
    onInputValueChange?.(value);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <CheckboxesTagsFE
      {...rest}
      className={clsx("SearchMultipleFE", className)}
      onChange={handleChange}
      onInputChange={handleInputChange}
      placeholder={t("global.search")}
      options={[]}
      freeSolo
    />
  );
}

export default SearchMultipleFE;
