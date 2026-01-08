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

import FieldEditorButtonGroup from "@/components/common/FieldEditorButtonGroup";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import TransformIcon from "@mui/icons-material/Transform";
import { Button } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface Props {
  defaultColumnCount: number;
  maxColumns: number;
  onResize: (value: number) => void;
}

function ColumnsResize({ defaultColumnCount: columnCount, maxColumns, onResize }: Props) {
  const { t } = useTranslation();
  const [resizeValue, setResizeValue] = useState(columnCount);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = Number(event.target.value);
    setResizeValue(R.clamp(1, maxColumns, value));
  };

  const handleClick = () => {
    onResize(resizeValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FieldEditorButtonGroup size="extra-small" tooltip={t("global.resize")}>
      <NumberFE value={resizeValue} onChange={handleChange} sx={{ width: 75 }} />
      <Button disabled={resizeValue === columnCount} onClick={handleClick}>
        <TransformIcon />
      </Button>
    </FieldEditorButtonGroup>
  );
}

export default ColumnsResize;
