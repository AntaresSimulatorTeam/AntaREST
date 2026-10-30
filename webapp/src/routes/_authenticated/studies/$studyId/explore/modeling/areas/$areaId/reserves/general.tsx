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

import DataTable from "@/components/DataTable";
import type { MainRowData } from "@/components/DataTable/types";
import RefetchErrorAlert from "@/components/queries/RefetchErrorAlert";
import { reserveKeys } from "@/queries/reserves/keys";
import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import EditIcon from "@mui/icons-material/Edit";
import { Button, Chip } from "@mui/material";
import { useIsMutating, useSuspenseQueries } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import CreateReserveDialog from "./-components/CreateReserveDialog";
import UpdateGlobalParametersDrawer from "./-components/UpdateGlobalParametersDrawer";
import UpdateReserveDrawer from "./-components/UpdateReserveDrawer";
import useCreateReserve from "./-hooks/useCreateReserve";
import useDeleteReserves from "./-hooks/useDeleteReserves";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/general",
)({
  component: ReservesGeneral,
});

const columnHelper = createMRTColumnHelper<Reserve>();

const columns = [
  columnHelper.accessor("type", {
    header: "Type",
    Cell: ({ cell }) => (
      <Chip
        label={cell.getValue()}
        size="small"
        color={cell.getValue() === "up" ? "success" : "warning"}
        variant="outlined"
        sx={{ borderRadius: 1, textTransform: "uppercase" }}
      />
    ),
  }),
  columnHelper.accessor("failureCost", { header: "Failure Cost" }),
  columnHelper.accessor("spillageCost", { header: "Spillage Cost" }),
  columnHelper.accessor("referenceActivationDuration", {
    header: "Ref. Activation Duration",
  }),
  columnHelper.accessor("powerActivationRatio", { header: "Power Activation Ratio" }),
  columnHelper.accessor("energyActivationRatio", { header: "Energy Activation Ratio" }),
];

function ReservesGeneral() {
  const { t } = useTranslation();
  const params = Route.useParams();
  const [editingReserve, setEditingReserve] = useState<Reserve | null>(null);
  const [isUpdateReserveOpen, setIsUpdateReserveOpen] = useState(false);
  const [isGlobalParametersOpen, setIsGlobalParametersOpen] = useState(false);
  const createReserve = useCreateReserve(params);
  const deleteReserves = useDeleteReserves(params);
  const { studyId, areaId } = params;

  const [{ data: isReservesEnabled }, { data: reserves, error, isRefetchError }] =
    useSuspenseQueries({
      queries: [reserveQueries.enabled(studyId), reserveQueries.list(studyId, areaId)],
    });

  const isSaving =
    useIsMutating({
      mutationKey: reserveKeys.list(studyId, areaId),
    }) !== 0;

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleNameClick = (row: Reserve) => {
    setEditingReserve(row);
    setIsUpdateReserveOpen(true);
  };

  const handleCreate = ({ name }: MainRowData, type: Reserve["type"]) => {
    return createReserve.mutate({ data: { name, type } });
  };

  const handleDuplicate = (row: Reserve, newName: string) => {
    return createReserve.mutate({
      data: { ...row, name: newName },
    });
  };

  const handleDelete = (rowsToDelete: Reserve[]) => {
    return deleteReserves.mutate({
      reserveIds: rowsToDelete.map((row) => row.id),
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <RefetchErrorAlert isRefetchError={isRefetchError} error={error} />
      <DataTable
        data={reserves}
        columns={columns}
        readOnly={!isReservesEnabled}
        isSaving={isSaving}
        onCreate={handleCreate}
        renderCreateDialog={({ open, onClose, onSubmit, existingNames }) => (
          <CreateReserveDialog
            open={open}
            onClose={onClose}
            onSubmit={(values) => onSubmit({ name: values.name }, values.type)}
            existingNames={existingNames}
          />
        )}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
        onNameClick={handleNameClick}
        deleteConfirmationMessage={(rowsToDelete) =>
          t("study.modeling.reserves.question.delete", {
            count: rowsToDelete.length,
            names: rowsToDelete.map((row) => row.name),
          })
        }
        toolbarActions={
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => setIsGlobalParametersOpen(true)}
            disabled={!isReservesEnabled}
          >
            {t("study.modeling.reserves.globalParameters")}
          </Button>
        }
      />
      {editingReserve && (
        <UpdateReserveDrawer
          open={isUpdateReserveOpen}
          reserve={editingReserve}
          onClose={() => setIsUpdateReserveOpen(false)}
        />
      )}
      <UpdateGlobalParametersDrawer
        open={isGlobalParametersOpen}
        onClose={() => setIsGlobalParametersOpen(false)}
      />
    </>
  );
}
