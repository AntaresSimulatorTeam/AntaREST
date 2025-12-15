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

import EmptyView from "@/components/page/EmptyView";
import ListView from "@/components/page/ListView";
import ViewWrapper from "@/components/page/ViewWrapper";
import useDialog from "@/hooks/useDialog";
import { sortByName } from "@/services/utils";
import AddIcon from "@mui/icons-material/Add";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { Button } from "@mui/material";
import { createFileRoute, linkOptions, redirect } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";
import storage, { StorageKey } from "../../../../../../services/utils/localStorage";
import TableTemplateFormDialog from "./$tableModeId/-components/TableTemplateFormDialog";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/tablemode")({
  loader: ({ params: { studyId }, location }) => {
    const templates = storage.getItem(StorageKey.StudiesModelTableModeTemplates) || [];
    const sortedTemplates = sortByName(templates);

    if (
      sortedTemplates.length > 0 &&
      location.pathname === `/studies/${studyId}/explore/tablemode`
    ) {
      throw redirect({
        to: "/studies/$studyId/explore/tablemode/$tableModeId",
        params: { studyId, tableModeId: sortedTemplates[0].name },
        replace: true,
      });
    }

    return sortedTemplates;
  },
  component: TableModeLayout,
});

function TableModeLayout() {
  const templates = Route.useLoaderData();
  const study = useStudy();
  const { t } = useTranslation();
  const { openDialog } = useDialog();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAdd = () => {
    openDialog(({ onClose }) => (
      <TableTemplateFormDialog
        title={t("study.tableMode.dialog.add.title")}
        titleIcon={AddCircleIcon}
        defaultValues={{
          name: "",
          type: "areas",
          columns: [],
        }}
        onCancel={onClose}
        templates={templates}
      />
    ));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ListView
      splitId="tablemode"
      list={templates.map((tp) => ({
        id: tp.name,
        label: tp.name,
        linkOptions: linkOptions({
          to: "/studies/$studyId/explore/tablemode/$tableModeId",
          params: { studyId: study.id, tableModeId: tp.name },
        }),
      }))}
      renderPanel={ViewWrapper}
      renderEmptyPanel={() => <EmptyView title={t("study.tableMode.empty")} />}
      actions={
        <Button startIcon={<AddIcon />} variant="contained" onClick={handleAdd}>
          {t("global.add")}
        </Button>
      }
    />
  );
}
