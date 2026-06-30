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

import ViewWrapper from "@/components/page/ViewWrapper";
import TableModeDataForm from "@/components/TableModeDataForm";
import useDialog from "@/hooks/useDialog";
import { isQueryListItemOptimistic } from "@/queries/utils";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Button } from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useDeleteTableMode from "../-hooks/useDeleteTableMode";
import UpdateTableModeDialog from "./-components/UpdateTableModeDialog";
import useTableMode from "./-hooks/useTableMode";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/table-modes/$tableModeId/",
)({
  component: TableMode,
});

function TableMode() {
  const { studyId } = Route.useParams();
  const { t } = useTranslation();
  const { openDialog, confirm } = useDialog();
  const navigate = Route.useNavigate();
  const tableMode = useTableMode();
  const isOptimistic = isQueryListItemOptimistic(tableMode);
  const deleteTableMode = useDeleteTableMode();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleEdit = () => {
    if (!tableMode) {
      return;
    }

    openDialog(({ onClose }) => <UpdateTableModeDialog tableMode={tableMode} onCancel={onClose} />);
  };

  const handleDelete = async () => {
    if (!tableMode) {
      return;
    }

    const isConfirmed = await confirm({
      titleIcon: DeleteIcon,
      alert: "error",
      content: t("study.tableModes.dialog.delete.text", {
        name: tableMode.name,
      }),
    });

    if (isConfirmed) {
      deleteTableMode.mutate({ tableId: tableMode.id });

      navigate({ to: "..", replace: true });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <TableModeDataForm
        studyId={studyId}
        name={tableMode.name}
        type={tableMode.type}
        columns={tableMode.columns}
        extraActions={
          <>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={handleEdit}
              disabled={isOptimistic}
            >
              {t("global.edit")}
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleDelete}
              disabled={isOptimistic}
            >
              {t("global.delete")}
            </Button>
          </>
        }
      />
    </ViewWrapper>
  );
}
