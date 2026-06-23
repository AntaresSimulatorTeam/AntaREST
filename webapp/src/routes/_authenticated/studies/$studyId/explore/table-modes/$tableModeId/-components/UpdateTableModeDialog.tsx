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

import type { SubmitHandlerPlus } from "@/components/Form/types";
import type { TableMode } from "@/services/api/tablemode/types";
import EditIcon from "@mui/icons-material/Edit";
import { useTranslation } from "react-i18next";
import useUpdateTableMode from "../../-hooks/useUpdateTableMode";
import TableModeFormDialog from "./BaseTableModeDialog";

interface Props {
  tableMode: TableMode;
  onCancel: VoidFunction;
}

function UpdateTableModeDialog({ tableMode, onCancel }: Props) {
  const { t } = useTranslation();
  const updateTableMode = useUpdateTableMode();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<TableMode>) => {
    const { id, ...update } = values;
    updateTableMode.mutate({ tableId: id, ...update });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableModeFormDialog
      title={t("study.tableModes.dialog.edit.title")}
      titleIcon={EditIcon}
      defaultValues={tableMode}
      onCancel={onCancel}
      onSubmit={handleSubmit}
    />
  );
}

export default UpdateTableModeDialog;
