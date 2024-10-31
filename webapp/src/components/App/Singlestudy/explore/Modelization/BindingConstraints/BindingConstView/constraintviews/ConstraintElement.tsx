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

import { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { FormControlLabel, Switch, Typography } from "@mui/material";

import { ConstraintElementData, ConstraintElementRoot } from "./style";

interface ElementProps {
  left: ReactNode;
  right: ReactNode;
  operator?: string;
  isLink?: boolean;
  onToggleType?: () => void;
}

function ConstraintElement({
  isLink,
  left,
  right,
  operator = "x",
  onToggleType,
}: ElementProps) {
  const { t } = useTranslation();

  return (
    <ConstraintElementRoot>
      <ConstraintElementData>
        {onToggleType !== undefined && (
          <FormControlLabel
            control={<Switch checked={isLink === true} />}
            onChange={(event, checked) => onToggleType()}
            label={isLink ? t("study.link") : t("study.cluster")}
            labelPlacement="bottom"
          />
        )}
        {left}
        <Typography sx={{ mx: 1 }}>{operator}</Typography>
        {right}
      </ConstraintElementData>
    </ConstraintElementRoot>
  );
}

export default ConstraintElement;
