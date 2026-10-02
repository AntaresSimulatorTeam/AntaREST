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

import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import type { ProductionType } from "@/services/api/studies/areas/reserves/types";
import { Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { PRODUCTION_TYPE_OPTIONS } from "../-productionTypes";

interface Props {
  value: ProductionType;
  onChange: (value: ProductionType) => void;
  disabled?: boolean;
  disabledReason?: string;
}

function ProductionTypeSelect({ value, onChange, disabled, disabledReason }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: SelectFEChangeEvent<ProductionType>) => {
    onChange(event.target.value);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip title={disabled && disabledReason ? disabledReason : ""}>
      <span>
        <SelectFE
          label={t("study.modeling.reserves.productionType")}
          value={value}
          options={PRODUCTION_TYPE_OPTIONS}
          onChange={handleChange}
          disabled={disabled}
          size="extra-small"
          sx={{ width: 180 }}
        />
      </span>
    </Tooltip>
  );
}

export default ProductionTypeSelect;
