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

import EmptyView from "@/components/page/EmptyView";
import ListView from "@/components/page/ListView";
import useDialog from "@/hooks/useDialog";
import { getNames, sortByName } from "@/services/utils";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import TableViewIcon from "@mui/icons-material/TableView";
import { createFileRoute, linkOptions, redirect } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
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
        from: Route.fullPath,
        to: "$tableModeId",
        params: { tableModeId: sortedTemplates[0].name },
        replace: true,
      });
    }

    return sortedTemplates;
  },
  component: TableModeLayout,
});

function TableModeLayout() {
  const templates = Route.useLoaderData();
  const existingNames = Route.useLoaderData({ select: getNames });
  const params = Route.useParams();
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
        existingNames={existingNames}
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
          params: { ...params, tableModeId: tp.name },
        }),
      }))}
      emptyListContent={<EmptyView title={t("study.tableMode.empty")} icon={TableViewIcon} />}
      onAdd={handleAdd}
    />
  );
}
