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

import SelectFE from "@/components/fieldEditors/SelectFE";
import { useTranslation } from "react-i18next";
import type { MonteCarloMode } from "../../../-utils";

interface MonteCarloModeSelectorProps {
  value: MonteCarloMode;
  onChange: (mode: MonteCarloMode) => void;
  disabled?: boolean;
}

function MonteCarloModeSelector({ value, onChange, disabled }: MonteCarloModeSelectorProps) {
  const { t } = useTranslation();

  return (
    <SelectFE
      label={t("study.outputs.monteCarlo")}
      value={value}
      options={[
        { value: "mc-all", label: "Synthesis" },
        { value: "mc-ind", label: "Year by year" },
        { value: "variable-per-variable", label: t("study.outputs.variablePerVariable") },
      ]}
      size="extra-small"
      onChange={(event) => onChange(event.target.value)}
      margin="dense"
      disabled={disabled}
      sx={{ minWidth: 150 }}
    />
  );
}

export default MonteCarloModeSelector;
