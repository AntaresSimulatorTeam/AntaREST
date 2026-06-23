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
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useTranslation } from "react-i18next";
import useCreateTableMode from "../../-hooks/useCreateTableMode";
import TableModeFormDialog from "./BaseTableModeDialog";

interface Props {
  onCancel: VoidFunction;
}

function AddTableModeDialog({ onCancel }: Props) {
  const { t } = useTranslation();
  const createTableMode = useCreateTableMode();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<TableMode>) => {
    createTableMode.mutate(values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TableModeFormDialog
      title={t("study.tableModes.dialog.add.title")}
      titleIcon={AddCircleIcon}
      defaultValues={{
        id: "",
        name: "",
        type: "areas",
        columns: [],
      }}
      onCancel={onCancel}
      onSubmit={handleSubmit}
    />
  );
}

export default AddTableModeDialog;
