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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useFormBlocker from "@/hooks/useFormBlocker";
import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import { thermalQueries } from "@/queries/thermals/queries";
import {
  adaptClusterGroupsToReservesSymmetriesDto,
  adaptReservesSymmetriesDtoToClusterGroups,
} from "@/services/api/studies/areas/reserves/adapters";
import type {
  ClusterGroup,
  SymmetryProductionType,
} from "@/services/api/studies/areas/reserves/types";
import { toError } from "@/utils/fnUtils";
import { Alert } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import useUndo from "use-undo";
import SymmetriesTable from "./-components/SymmetriesTable";
import {
  addSymmetries,
  deleteSymmetryRows,
  duplicateSymmetryRow,
  toggleReserve,
  validateGroups,
} from "./-components/SymmetriesTable/utils";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/symmetries",
)({
  component: ReservesSymmetries,
});

// Only thermal clusters have a symmetries endpoint today. "storages" and
// "hydro" are coming soon: add them to a selector once their endpoints are
// released, the rest of this screen is already parameterized by this value.
const PRODUCTION_TYPE: SymmetryProductionType = "thermals";

function ReservesSymmetries() {
  const { studyId, areaId } = Route.useParams();

  // The router doesn't remount on param-only changes: the key re-seeds the
  // editable state (undo history, `lastSaved`) when the area/study changes.
  return <SymmetriesView key={`${studyId}-${areaId}`} />;
}

function SymmetriesView() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { data: reservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));

  const { data: reserves, isFetching: isReservesFetching } = useSuspenseQuery(
    reserveQueries.list(studyId, areaId),
  );

  const { data: thermalClusters, isFetching: isThermalsFetching } = useSuspenseQuery(
    thermalQueries.list(studyId, areaId),
  );

  const { data: thermalCertifications, isFetching: isCertificationsFetching } = useSuspenseQuery(
    reserveQueries.certifications(studyId, areaId, "thermals"),
  );

  const { data: symmetriesData, isFetching: isSymmetriesFetching } = useSuspenseQuery(
    reserveQueries.symmetries(studyId, areaId, PRODUCTION_TYPE),
  );

  // Inverted from { reserveId: { clusterId: ... } } to { clusterId: Set<reserveId> },
  // used to gate which checkboxes are checkable: a cluster can only be marked
  // symmetric on a reserve it's certified for.
  const certifiedReservesByCluster = useMemo(() => {
    const map = new Map<string, Set<string>>();

    for (const [reserveId, clusters] of Object.entries(thermalCertifications)) {
      for (const clusterId of Object.keys(clusters)) {
        const reserveIds = map.get(clusterId) ?? new Set<string>();
        reserveIds.add(reserveId);
        map.set(clusterId, reserveIds);
      }
    }

    return map;
  }, [thermalCertifications]);

  const initialGroups = useMemo(
    () => adaptReservesSymmetriesDtoToClusterGroups(thermalClusters, symmetriesData),
    [thermalClusters, symmetriesData],
  );

  const [
    { present: groups },
    { set: setGroups, reset: resetGroups, undo, redo, canUndo, canRedo },
  ] = useUndo<ClusterGroup[]>(initialGroups);

  const [lastSaved, setLastSaved] = useState(initialGroups);
  const [isSaving, setIsSaving] = useState(false);

  // Reference comparison, same rationale as `DataGridForm`: deep comparison
  // would work too but doesn't scale to a large matrix.
  const isDirty = lastSaved !== groups;

  // The queries refetch on every mount and window focus (EXTERNALLY_MUTATED):
  // adopt fresh data while there's no unsaved edit, so Save never re-PUTs a
  // stale snapshot.
  useEffect(() => {
    if (!isDirty && groups !== initialGroups) {
      resetGroups(initialGroups);
      setLastSaved(initialGroups);
    }
  }, [groups, initialGroups, isDirty, resetGroups]);

  const validationErrors = useMemo(() => validateGroups(groups), [groups]);

  useFormBlocker({ isSubmitting: isSaving, isDirty });

  const updateSymmetriesMutation = useMutation(
    reserveMutations.updateSymmetries(studyId, areaId, PRODUCTION_TYPE),
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleAddSymmetries = (clusterId: string, count: number) => {
    setGroups(addSymmetries(groups, clusterId, count));
  };

  const handleDeleteRows = (uiIds: Set<string>) => {
    setGroups(deleteSymmetryRows(groups, uiIds));
  };

  const handleDuplicateRow = (uiId: string) => {
    setGroups(duplicateSymmetryRow(groups, uiId));
  };

  const handleToggleReserve = (uiId: string, reserveId: string) => {
    setGroups(toggleReserve(groups, uiId, reserveId));
  };

  const handleSave = async () => {
    if (validationErrors.length > 0) {
      return;
    }

    setIsSaving(true);

    try {
      const updatedSymmetries = await updateSymmetriesMutation.mutateAsync({
        studyId,
        areaId,
        productionType: PRODUCTION_TYPE,
        data: adaptClusterGroupsToReservesSymmetriesDto(groups),
      });

      // The response is the server-normalized payload; the resync effect
      // adopts it once `lastSaved` marks the form pristine.
      queryClient.setQueryData(
        reserveQueries.symmetries(studyId, areaId, PRODUCTION_TYPE).queryKey,
        updatedSymmetries,
      );

      setLastSaved(groups);
    } catch (err) {
      enqueueErrorSnackbar(t("form.submit.error"), toError(err));
    } finally {
      setIsSaving(false);
    }
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
      <SymmetriesTable
        groups={groups}
        reserves={reserves}
        certifiedReservesByCluster={certifiedReservesByCluster}
        validationErrors={validationErrors}
        readOnly={!reservesEnabled}
        isFetching={
          isReservesFetching ||
          isThermalsFetching ||
          isCertificationsFetching ||
          isSymmetriesFetching
        }
        canUndo={canUndo}
        canRedo={canRedo}
        canSave={isDirty}
        isSaving={isSaving}
        onAddSymmetries={handleAddSymmetries}
        onDeleteRows={handleDeleteRows}
        onDuplicateRow={handleDuplicateRow}
        onToggleReserve={handleToggleReserve}
        onUndo={undo}
        onRedo={redo}
        onSave={handleSave}
      />
    </>
  );
}
