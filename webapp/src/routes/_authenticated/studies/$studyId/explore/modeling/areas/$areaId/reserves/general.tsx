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
import type { Reserve } from "@/services/api/studies/areas/reserves/types";
import { Alert, Chip } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { createMRTColumnHelper } from "material-react-table";
import { useTranslation } from "react-i18next";
import CreateReserveDialog from "./-components/CreateReserveDialog";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/general",
)({
  loader: async ({ context, params: { studyId, areaId } }) => {
    await context.queryClient.ensureQueryData(reserveQueries.list(studyId, areaId));
  },
  component: ReservesGeneral,
});

interface ReserveRow extends Reserve {
  name: string;
}

function reserveToRow(reserve: Reserve): ReserveRow {
  return { ...reserve, name: reserve.id };
}

function reservesToRows(reserves: Reserve[]): ReserveRow[] {
  return reserves.map(reserveToRow);
}

const columnHelper = createMRTColumnHelper<ReserveRow>();

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

  // Reserves are editable only when enabled in the optimization configuration
  // ("includeReserves"). Otherwise the table is shown in read-only mode.
  const { data: reservesEnabled } = useSuspenseQuery(reserveQueries.includeReserves(studyId));

  const { queryKey: listQueryKey } = reserveQueries.list(studyId, areaId);

  const { data: rows } = useSuspenseQuery({
    ...reserveQueries.list(studyId, areaId),
    select: reservesToRows,
  });

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

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleCreate = async ({ name, type }: RowData & Partial<ReserveRow>) => {
    // `type` is always set: it's a required field of the create dialog
    if (!type) {
      throw new Error("Reserve type is required");
    }

    const newReserve = await createMutation.mutateAsync({
      studyId,
      areaId,
      data: { id: name, type },
    });

    return reserveToRow(newReserve);
  };

  const handleDuplicate = async (row: ReserveRow, newName: string) => {
    // The extra `name` row prop is stripped by the create input schema
    const newReserve = await createMutation.mutateAsync({
      studyId,
      areaId,
      data: { ...row, id: newName },
    });

    return reserveToRow(newReserve);
  };

  const handleDelete = (rowsToDelete: ReserveRow[]) => {
    return deleteMutation.mutateAsync({
      studyId,
      areaId,
      reserveIds: rowsToDelete.map((row) => row.id),
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
        deleteConfirmationMessage={(rowsToDelete) =>
          t("study.modeling.reserves.question.delete", {
            count: rowsToDelete.length,
            reserveNames: rowsToDelete.map((row) => row.name),
          })
        }
      />
    </>
  );
}
