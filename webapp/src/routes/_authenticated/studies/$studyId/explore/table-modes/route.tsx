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
import TableViewIcon from "@mui/icons-material/TableView";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import AddTableModeDialog from "./$tableModeId/-components/AddTableModeDialog";
import MigrationTableModes from "./$tableModeId/-components/MigrationTableModes";
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
    <>
      <RouterListView
        splitId="table-modes"
        list={list}
        emptyListView={<EmptyView title={t("study.tableModes.empty")} icon={TableViewIcon} />}
        onAdd={handleAdd}
      />
      <MigrationTableModes />
    </>
  );
}
