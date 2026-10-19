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

import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type {
  ProductionType,
  Reserve,
  ReserveCertification,
} from "@/services/api/studies/areas/reserves/types";
import { Alert } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQueries } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useTransition } from "react";
import { useTranslation } from "react-i18next";
import CertificationsTable, {
  type AssetRow,
  type ReserveRow,
} from "./-components/CertificationsTable";
import ProductionTypeSelect from "./-components/ProductionTypeSelect";
import UpdateCertificationDrawer from "./-components/UpdateCertificationDrawer";
import UpdateReserveAssetsDrawer from "./-components/UpdateReserveAssetsDrawer";
import { DEFAULT_PRODUCTION_TYPE, PRODUCTION_TYPES } from "./-productionTypes";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/certifications",
)({
  component: ReservesCertifications,
});

function ReservesCertifications() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();
  const queryClient = useQueryClient();
  const [productionType, setProductionType] = useState(DEFAULT_PRODUCTION_TYPE);
  // Switching type suspends on new queries: the transition keeps the current
  // table on screen (with its loading state) instead of the route fallback.
  const [isProductionTypePending, startProductionTypeTransition] = useTransition();
  const [selectedReserve, setSelectedReserve] = useState<Reserve | null>(null);
  const [isAssetsDrawerOpen, setIsAssetsDrawerOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<AssetRow | null>(null);
  const [isUpdateDrawerOpen, setIsUpdateDrawerOpen] = useState(false);

  const { labelKey, assetsQuery, defaultCertification } = PRODUCTION_TYPES[productionType];

  const [
    { data: reservesEnabled },
    { data: reserves, isFetching: isReservesFetching },
    { data: certifications },
    { data: assets },
  ] = useSuspenseQueries({
    queries: [
      reserveQueries.enabled(studyId),
      reserveQueries.list(studyId, areaId),
      reserveQueries.certifications(studyId, areaId, productionType),
      assetsQuery(studyId, areaId),
    ],
  });

  const updateMutation = useMutation({
    ...reserveMutations.updateCertifications(studyId, areaId, productionType),
    onSuccess: (updatedCertifications, { productionType }) => {
      queryClient.setQueryData(
        reserveQueries.certifications(studyId, areaId, productionType).queryKey,
        updatedCertifications,
      );
    },
  });

  const rows = useMemo<ReserveRow[]>(() => {
    const assetsById = new Map(assets.map((asset) => [asset.id, asset]));

    return reserves.map((reserve) => ({
      kind: "reserve",
      id: reserve.id,
      name: reserve.name,
      reserve,
      subRows: Object.entries(certifications[reserve.id] ?? {}).map(
        ([assetId, certification]): AssetRow => ({
          kind: "asset",
          // Prefixed with the reserve ID because an asset can be certified for
          // several reserves and row IDs must be unique across the table
          id: `${reserve.id}/${assetId}`,
          name: assetsById.get(assetId)?.name ?? assetId,
          enabled: assetsById.get(assetId)?.enabled,
          productionType,
          reserveId: reserve.id,
          assetId,
          certification,
        }),
      ),
    }));
  }, [reserves, certifications, assets, productionType]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleProductionTypeChange = (type: ProductionType) => {
    // Drawers hold rows of the current type: don't let them outlive it.
    setSelectedReserve(null);
    setEditingAsset(null);
    startProductionTypeTransition(() => setProductionType(type));
  };

  const handleReserveClick = ({ reserve }: ReserveRow) => {
    setSelectedReserve(reserve);
    setIsAssetsDrawerOpen(true);
  };

  const handleAssetClick = (row: AssetRow) => {
    setEditingAsset(row);
    setIsUpdateDrawerOpen(true);
  };

  // Rebuilds the reserve's mapping from the selection: kept assets retain their
  // parameters, new ones get the defaults, deselected ones are removed (the PUT
  // endpoint replaces the whole mapping).
  const handleAssetsSubmit = async (assetIds: string[]) => {
    if (!selectedReserve) {
      return assetIds;
    }

    const currentReserveCertifications = certifications[selectedReserve.id] ?? {};

    const reserveCertifications = Object.fromEntries(
      assetIds.map((assetId) => [
        assetId,
        currentReserveCertifications[assetId] ?? defaultCertification,
      ]),
    );

    const data = { ...certifications };

    if (assetIds.length > 0) {
      data[selectedReserve.id] = reserveCertifications;
    } else {
      delete data[selectedReserve.id];
    }

    const updatedCertifications = await updateMutation.mutateAsync({
      studyId,
      areaId,
      productionType,
      data,
    });

    return Object.keys(updatedCertifications[selectedReserve.id] ?? {});
  };

  const handleCertificationSubmit = async (certification: ReserveCertification) => {
    if (!editingAsset) {
      return certification;
    }

    const { reserveId, assetId } = editingAsset;

    const data = {
      ...certifications,
      [reserveId]: {
        ...certifications[reserveId],
        [assetId]: certification,
      },
    };

    const updatedCertifications = await updateMutation.mutateAsync({
      studyId,
      areaId,
      productionType,
      data,
    });

    return updatedCertifications[reserveId]?.[assetId] ?? certification;
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
      <CertificationsTable
        rows={rows}
        productionType={productionType}
        toolbarActions={
          <ProductionTypeSelect value={productionType} onChange={handleProductionTypeChange} />
        }
        readOnly={!reservesEnabled}
        isLoading={isReservesFetching || isProductionTypePending}
        onReserveClick={handleReserveClick}
        onAssetClick={handleAssetClick}
      />
      {selectedReserve && (
        <UpdateReserveAssetsDrawer
          key={`${productionType}/${selectedReserve.id}`}
          open={isAssetsDrawerOpen}
          reserveName={selectedReserve.name}
          label={t(labelKey)}
          assets={assets}
          defaultValues={Object.keys(certifications[selectedReserve.id] ?? {})}
          onClose={() => setIsAssetsDrawerOpen(false)}
          onSubmit={handleAssetsSubmit}
        />
      )}
      {editingAsset && (
        <UpdateCertificationDrawer
          key={`${productionType}/${editingAsset.id}`}
          open={isUpdateDrawerOpen}
          productionType={productionType}
          assetName={editingAsset.name}
          assetEnabled={editingAsset.enabled}
          certification={editingAsset.certification}
          onClose={() => setIsUpdateDrawerOpen(false)}
          onSubmit={handleCertificationSubmit}
        />
      )}
    </>
  );
}
