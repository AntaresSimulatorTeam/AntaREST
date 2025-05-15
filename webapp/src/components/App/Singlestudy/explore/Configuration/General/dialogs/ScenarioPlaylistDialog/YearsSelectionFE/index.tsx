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

import StringFE from "@/components/common/fieldEditors/StringFE";
import { Tooltip } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  isSelectionsValid,
  selectionsToNumbers,
  selectionsToString,
  stringToSelection,
} from "./utils";

interface Props {
  maxYears: number;
  onChange: (years: number[]) => void;
}

function YearsSelectionFE({ maxYears, onChange }: Props) {
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
    const isValid = isSelectionsValid(selectionsValue, maxYears);

    setError(!isValid);

    if (!isValid) {
      onChange([]);
      return;
    }

    const selections = stringToSelection(selectionsValue);
    // If no selections, we return all years
    const years =
      selections.length === 0 ? R.range(1, maxYears + 1) : selectionsToNumbers(selections);

    setSelectionsValue(selectionsToString(selections));
    onChange(years);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip
      title={
        error
          ? t("study.configuration.general.mcScenarioPlaylist.yearsSelection.error")
          : selectionsValue.trim()
      }
      placement="top"
      disableFocusListener
    >
      <span>
        <StringFE
          label={t("study.configuration.general.mcScenarioPlaylist.yearsSelection.label")}
          placeholder={t(
            "study.configuration.general.mcScenarioPlaylist.yearsSelection.placeholder",
          )}
          value={selectionsValue}
          onChange={handleChange}
          onBlur={handleBlur}
          size="extra-small"
          error={error}
        />
      </span>
    </Tooltip>
  );
}

export default YearsSelectionFE;
