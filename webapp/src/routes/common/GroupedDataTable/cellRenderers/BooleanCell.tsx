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

import { Chip } from "@mui/material";
import type { MRT_Cell, MRT_RowData } from "material-react-table";
import { useTranslation } from "react-i18next";

interface Props<T extends MRT_RowData> {
  cell: MRT_Cell<T, boolean>;
}

function BooleanCell<T extends MRT_RowData>({ cell }: Props<T>) {
  const { t } = useTranslation();

  return (
    <Chip
      label={cell.getValue() ? t("button.yes") : t("button.no")}
      color={cell.getValue() ? "success" : "error"}
      sx={{ minWidth: 40 }}
    />
  );
}

export default BooleanCell;
