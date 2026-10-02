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
import {
  adaptClusterGroupsToReservesSymmetriesDto,
  adaptReservesSymmetriesDtoToClusterGroups,
} from "@/services/api/studies/areas/reserves/adapters";
import type { ProductionType } from "@/services/api/studies/areas/reserves/types";
import { toError } from "@/utils/fnUtils";
import { Alert } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQueries } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState, useTransition } from "react";
import { useTranslation } from "react-i18next";
import useUndo from "use-undo";
import ProductionTypeSelect from "./-components/ProductionTypeSelect";
import SymmetriesTable from "./-components/SymmetriesTable";
import type { ClusterGroup } from "./-components/SymmetriesTable/types";
import {
  addSymmetries,
  deleteSymmetryRows,
  duplicateSymmetryRow,
  toggleReserve,
  validateGroups,
} from "./-components/SymmetriesTable/utils";
import { DEFAULT_PRODUCTION_TYPE, PRODUCTION_TYPES } from "./-productionTypes";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/symmetries",
)({
  component: ReservesSymmetries,
});

function ReservesSymmetries() {
  const { studyId, areaId } = Route.useParams();
  const [productionType, setProductionType] = useState(DEFAULT_PRODUCTION_TYPE);
  // Switching type suspends on new queries: the transition keeps the current
  // table on screen (with a progress bar) instead of the route fallback.
  const [isProductionTypePending, startProductionTypeTransition] = useTransition();

  const handleProductionTypeChange = (type: ProductionType) => {
    startProductionTypeTransition(() => setProductionType(type));
  };

  // The router doesn't remount on param-only changes: the key re-seeds the
  // editable state (undo history, `lastSaved`) when the area/study or the
  // production type changes.
  return (
    <SymmetriesView
      key={`${studyId}-${areaId}-${productionType}`}
      productionType={productionType}
      isProductionTypePending={isProductionTypePending}
      onProductionTypeChange={handleProductionTypeChange}
    />
  );
}

interface SymmetriesViewProps {
  productionType: ProductionType;
  isProductionTypePending: boolean;
  onProductionTypeChange: (type: ProductionType) => void;
}

function SymmetriesView({
  productionType,
  isProductionTypePending,
  onProductionTypeChange,
}: SymmetriesViewProps) {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { assetsQuery } = PRODUCTION_TYPES[productionType];

  // Run all five queries in parallel instead of suspending on them one after
  // another: the parent route's loader only prefetches `enabled` and `list`.
  const [
    { data: reservesEnabled },
    { data: reserves, isFetching: isReservesFetching },
    { data: assets, isFetching: isAssetsFetching },
    { data: certifications, isFetching: isCertificationsFetching },
    { data: symmetriesData, isFetching: isSymmetriesFetching },
  ] = useSuspenseQueries({
    queries: [
      reserveQueries.enabled(studyId),
      reserveQueries.list(studyId, areaId),
      assetsQuery(studyId, areaId),
      reserveQueries.certifications(studyId, areaId, productionType),
      reserveQueries.symmetries(studyId, areaId, productionType),
    ],
  });

  // Inverted from { reserveId: { assetId: ... } } to { assetId: Set<reserveId> },
  // used to gate which checkboxes are checkable: an asset can only be marked
  // symmetric on a reserve it's certified for.
  const certifiedReservesByCluster = useMemo(() => {
    const map = new Map<string, Set<string>>();

    for (const [reserveId, assetCertifications] of Object.entries(certifications)) {
      for (const assetId of Object.keys(assetCertifications)) {
        const reserveIds = map.get(assetId) ?? new Set<string>();
        reserveIds.add(reserveId);
        map.set(assetId, reserveIds);
      }
    }

    return map;
  }, [certifications]);

  const initialGroups = useMemo(
    () => adaptReservesSymmetriesDtoToClusterGroups(assets, symmetriesData),
    [assets, symmetriesData],
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
    reserveMutations.updateSymmetries(studyId, areaId, productionType),
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleAddSymmetries = (clusterIds: string[], count: number) => {
    setGroups(addSymmetries(groups, clusterIds, count));
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
        productionType,
        data: adaptClusterGroupsToReservesSymmetriesDto(groups),
      });

      // The response is the server-normalized payload; the resync effect
      // adopts it once `lastSaved` marks the form pristine.
      queryClient.setQueryData(
        reserveQueries.symmetries(studyId, areaId, productionType).queryKey,
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
        toolbarActions={
          // Switching type remounts the view and would drop unsaved edits.
          <ProductionTypeSelect
            value={productionType}
            onChange={onProductionTypeChange}
            disabled={isDirty || isSaving || isProductionTypePending}
            disabledReason={t("study.modeling.reserves.productionType.unsavedChanges")}
          />
        }
        readOnly={!reservesEnabled}
        isFetching={
          isReservesFetching ||
          isAssetsFetching ||
          isCertificationsFetching ||
          isSymmetriesFetching ||
          isProductionTypePending
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
