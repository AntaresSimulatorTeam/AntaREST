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

import TableMode from "@/components/TableMode";
import useDialog from "@/hooks/useDialog";
import storage, { StorageKey } from "@/services/utils/localStorage";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Button } from "@mui/material";
import { createFileRoute, useLoaderData } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../../-hooks/useStudy";
import TableTemplateFormDialog from "./-components/TableTemplateFormDialog";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/tablemode/$tableModeId/",
)({
  component: Table,
});

function Table() {
  const study = useStudy();
  const { tableModeId } = Route.useParams();
  const { t } = useTranslation();
  const { openDialog, confirm } = useDialog();
  const navigate = Route.useNavigate();

  const templates = useLoaderData({
    from: "/_authenticated/studies/$studyId/explore/tablemode",
  });

  const template = templates.find(({ name }) => name === tableModeId);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleEdit = () => {
    if (!template) {
      return;
    }

    openDialog(({ onClose }) => (
      <TableTemplateFormDialog
        title={t("study.tableMode.dialog.edit.title")}
        titleIcon={EditIcon}
        defaultValues={template}
        templates={templates}
        onCancel={onClose}
      />
    ));
  };

  const handleDelete = async () => {
    if (!template) {
      return;
    }

    const isConfirmed = await confirm({
      titleIcon: DeleteIcon,
      alert: "error",
      content: t("study.tableMode.dialog.delete.text", {
        name: template.name,
      }),
    });

    if (isConfirmed) {
      storage.setItem(StorageKey.StudiesModelTableModeTemplates, (prev) => {
        const currentTemplates = prev || [];
        return currentTemplates?.filter(({ name }) => name !== template.name);
      });

      navigate({ to: "..", replace: true });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!template) {
    return null;
  }

  return (
    <TableMode
      studyId={study.id}
      name={template.name}
      type={template.type}
      columns={template.columns}
      extraActions={
        <>
          <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
            {t("global.edit")}
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
          >
            {t("global.delete")}
          </Button>
        </>
      }
    />
  );
}
