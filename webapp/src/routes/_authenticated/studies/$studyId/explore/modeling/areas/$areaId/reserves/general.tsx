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

import GroupedDataTable from "@/components/GroupedDataTable";
import type { RowData } from "@/components/GroupedDataTable/types";
import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve, UpdateReserveData } from "@/services/api/studies/areas/reserves/types";
import EditIcon from "@mui/icons-material/Edit";
import { Alert, Button, Chip } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import CreateReserveDialog from "./-components/CreateReserveDialog";
import UpdateGlobalParametersDrawer from "./-components/UpdateGlobalParametersDrawer";
import UpdateReserveDrawer from "./-components/UpdateReserveDrawer";

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
  const { studyId, areaId } = Route.useParams();
  const queryClient = useQueryClient();
  const [editingReserve, setEditingReserve] = useState<Reserve | null>(null);
  const [isUpdateReserveOpen, setIsUpdateReserveOpen] = useState(false);
  const [isGlobalParametersOpen, setIsGlobalParametersOpen] = useState(false);

  const { data: reservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));

  const { queryKey: listQueryKey } = reserveQueries.list(studyId, areaId);

  const { data: rows, isFetching: isRowsFetching } = useSuspenseQuery(
    reserveQueries.list(studyId, areaId),
  );

  const createMutation = useMutation({
    ...reserveMutations.create(studyId, areaId),
    onSuccess: (newReserve) => {
      queryClient.setQueryData(listQueryKey, (old = []) => [...old, newReserve]);
    },
  });

  const deleteMutation = useMutation({
    ...reserveMutations.delete(studyId, areaId),
    onSuccess: (data, { reserveIds }) => {
      queryClient.setQueryData(listQueryKey, (old = []) =>
        old.filter((reserve) => !reserveIds.includes(reserve.id)),
      );
    },
  });

  const updateMutation = useMutation({
    ...reserveMutations.update(studyId, areaId),
    onSuccess: (updatedReserve) => {
      queryClient.setQueryData(listQueryKey, (old = []) =>
        old.map((reserve) => (reserve.id === updatedReserve.id ? updatedReserve : reserve)),
      );
    },
  });

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleNameClick = (row: Reserve) => {
    setEditingReserve(row);
    setIsUpdateReserveOpen(true);
  };

  const handleCreate = ({ name, type }: RowData & Partial<Reserve>) => {
    if (!type) {
      throw new Error("Reserve type is required");
    }

    return createMutation.mutateAsync({
      studyId,
      areaId,
      data: { name, type },
    });
  };

  const handleDuplicate = (row: Reserve, newName: string) => {
    return createMutation.mutateAsync({
      studyId,
      areaId,
      data: { ...row, name: newName },
    });
  };

  const handleDelete = (rowsToDelete: Reserve[]) => {
    return deleteMutation.mutateAsync({
      studyId,
      areaId,
      reserveIds: rowsToDelete.map((row) => row.id),
    });
  };

  const handleUpdate = async (data: UpdateReserveData) => {
    if (!editingReserve) {
      return;
    }

    await updateMutation.mutateAsync({
      studyId,
      areaId,
      reserveId: editingReserve.id,
      data,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {reservesEnabled === false && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          {t("study.modeling.reserves.readOnly.alert")}
        </Alert>
      )}
      <GroupedDataTable
        key={`${studyId}-${areaId}`}
        data={rows}
        columns={columns}
        readOnly={!reservesEnabled}
        isLoading={isRowsFetching}
        onCreate={handleCreate}
        renderCreateDialog={({ open, onClose, onSubmit, existingNames }) => (
          <CreateReserveDialog
            open={open}
            onClose={onClose}
            onSubmit={onSubmit}
            existingNames={existingNames}
          />
        )}
        onDuplicate={handleDuplicate}
        onDelete={handleDelete}
        onNameClick={handleNameClick}
        deleteConfirmationMessage={(rowsToDelete) =>
          t("study.modeling.reserves.question.delete", {
            count: rowsToDelete.length,
            reserveNames: rowsToDelete.map((row) => row.name),
          })
        }
        toolbarActions={
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => setIsGlobalParametersOpen(true)}
            disabled={!reservesEnabled}
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
          onSubmit={handleUpdate}
        />
      )}
      <UpdateGlobalParametersDrawer
        open={isGlobalParametersOpen}
        onClose={() => setIsGlobalParametersOpen(false)}
      />
    </>
  );
}
