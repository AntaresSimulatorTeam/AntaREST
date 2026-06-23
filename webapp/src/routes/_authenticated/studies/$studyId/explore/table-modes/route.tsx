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
import RouterListView from "@/components/page/list/RouterListView";
import useDialog from "@/hooks/useDialog";
import { tableModeQueries } from "@/queries/tableMode/queries";
import { tableModeCreationSchema } from "@/services/api/tablemode/schemas";
import storage from "@/services/utils/localStorage";
import TableViewIcon from "@mui/icons-material/TableView";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useMount } from "react-use";
import AddTableModeDialog from "./$tableModeId/-components/AddTableModeDialog";
import useCreateTableMode from "./-hooks/useCreateTableMode";
import { tableModesToList } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/table-modes")({
  loader: async ({ context }) => {
    await context.queryClient.ensureQueryData(tableModeQueries.list());
  },
  component: TableModesLayout,
});

function TableModesLayout() {
  const { data: list } = useSuspenseQuery({
    ...tableModeQueries.list(),
    select: tableModesToList,
  });

  const { t } = useTranslation();
  const { openDialog } = useDialog();
  const createTableMode = useCreateTableMode();

  // Workaround to migrate table modes stored in localStorage to the new backend system (since v2.32.0).
  // It can be removed after a certain period of time when we are confident that most users have migrated.
  useMount(() => {
    const oldTableModes = storage.getItem("studies.model.tableMode.templates");
    storage.removeItem("studies.model.tableMode.templates");

    if (Array.isArray(oldTableModes)) {
      oldTableModes.forEach((value) => {
        if (tableModeCreationSchema.safeParse(value).success) {
          createTableMode.mutate(value);
        }
      });
    }
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAdd = () => {
    openDialog(({ onClose }) => <AddTableModeDialog onCancel={onClose} />);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <RouterListView
      splitId="table-modes"
      list={list}
      emptyListView={<EmptyView title={t("study.tableModes.empty")} icon={TableViewIcon} />}
      onAdd={handleAdd}
    />
  );
}
