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
import { thermalQueries } from "@/queries/thermals/queries";
import type {
  CertificationProductionType,
  Reserve,
  ReserveCertification,
  ReservesCertifications,
} from "@/services/api/studies/areas/reserves/types";
import { Alert } from "@mui/material";
import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import CertificationsTable, {
  type ClusterRow,
  type ReserveRow,
} from "./-components/CertificationsTable";
import UpdateCertificationDrawer from "./-components/UpdateCertificationDrawer";
import UpdateReserveClustersDrawer, {
  type ClustersFormValues,
} from "./-components/UpdateReserveClustersDrawer";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/certifications",
)({
  component: ReservesCertifications,
});

// A cluster newly selected for a reserve starts with these values: the warning
// shown in the table prompts the user to fill them in.
const DEFAULT_CERTIFICATION: ReserveCertification = {
  maxPower: 0,
  maxPowerOff: 0,
  participationCost: 0,
  participationCostOff: 0,
};

function ReservesCertifications() {
  const { t } = useTranslation();
  const { studyId, areaId } = Route.useParams();
  const queryClient = useQueryClient();
  const [selectedReserve, setSelectedReserve] = useState<Reserve | null>(null);
  const [isClustersDrawerOpen, setIsClustersDrawerOpen] = useState(false);
  const [editingCluster, setEditingCluster] = useState<ClusterRow | null>(null);
  const [isUpdateDrawerOpen, setIsUpdateDrawerOpen] = useState(false);

  const { data: reservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));

  const { data: reserves, isFetching: isReservesFetching } = useSuspenseQuery(
    reserveQueries.list(studyId, areaId),
  );

  const { data: thermalCertifications } = useSuspenseQuery(
    reserveQueries.certifications(studyId, areaId, "thermals"),
  );

  const { data: thermalClusters } = useSuspenseQuery(thermalQueries.list(studyId, areaId));

  // Certifications mapping per production type. "storages" and "hydro" will be
  // added once their endpoints are released.
  const certificationsByType: Record<CertificationProductionType, ReservesCertifications> = {
    thermals: thermalCertifications,
  };

  const updateMutation = useMutation({
    ...reserveMutations.updateCertifications(studyId, areaId, "thermals"),
    onSuccess: (updatedCertifications, { productionType }) => {
      queryClient.setQueryData(
        reserveQueries.certifications(studyId, areaId, productionType).queryKey,
        updatedCertifications,
      );
    },
  });

  const rows = useMemo<ReserveRow[]>(() => {
    const clustersById = new Map(thermalClusters.map((cluster) => [cluster.id, cluster]));

    return reserves.map((reserve) => ({
      kind: "reserve",
      id: reserve.id,
      name: reserve.name,
      reserve,
      subRows: Object.entries(thermalCertifications[reserve.id] ?? {}).map(
        ([clusterId, certification]): ClusterRow => ({
          kind: "cluster",
          // Prefixed with the reserve ID because a cluster can be certified for
          // several reserves and row IDs must be unique across the table
          id: `${reserve.id}/${clusterId}`,
          name: clustersById.get(clusterId)?.name ?? clusterId,
          enabled: clustersById.get(clusterId)?.enabled ?? false,
          productionType: "thermals",
          reserveId: reserve.id,
          clusterId,
          certification,
        }),
      ),
    }));
  }, [reserves, thermalCertifications, thermalClusters]);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleReserveClick = ({ reserve }: ReserveRow) => {
    setSelectedReserve(reserve);
    setIsClustersDrawerOpen(true);
  };

  const handleClusterClick = (row: ClusterRow) => {
    setEditingCluster(row);
    setIsUpdateDrawerOpen(true);
  };

  // Rebuilds each production type's mapping from the selection: kept clusters
  // retain their parameters, new ones get the defaults, deselected ones are
  // removed (the PUT endpoint replaces the whole mapping).
  const handleClustersSubmit = async (values: ClustersFormValues) => {
    if (!selectedReserve) {
      return values;
    }

    const submittedValues = { ...values };

    for (const [productionType, selectedIds] of Object.entries(values) as Array<
      [CertificationProductionType, string[]]
    >) {
      const currentCertifications = certificationsByType[productionType];
      const currentReserveCertifications = currentCertifications[selectedReserve.id] ?? {};

      const reserveCertifications = Object.fromEntries(
        selectedIds.map((clusterId) => [
          clusterId,
          currentReserveCertifications[clusterId] ?? DEFAULT_CERTIFICATION,
        ]),
      );

      const data = { ...currentCertifications };

      if (selectedIds.length > 0) {
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

      submittedValues[productionType] = Object.keys(
        updatedCertifications[selectedReserve.id] ?? {},
      );
    }

    return submittedValues;
  };

  const handleCertificationSubmit = async (certification: ReserveCertification) => {
    if (!editingCluster) {
      return certification;
    }

    const { productionType, reserveId, clusterId } = editingCluster;
    const currentCertifications = certificationsByType[productionType];

    const data = {
      ...currentCertifications,
      [reserveId]: {
        ...currentCertifications[reserveId],
        [clusterId]: certification,
      },
    };

    const updatedCertifications = await updateMutation.mutateAsync({
      studyId,
      areaId,
      productionType,
      data,
    });

    return updatedCertifications[reserveId]?.[clusterId] ?? certification;
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
        readOnly={!reservesEnabled}
        isLoading={isReservesFetching}
        onReserveClick={handleReserveClick}
        onClusterClick={handleClusterClick}
      />
      {selectedReserve && (
        <UpdateReserveClustersDrawer
          key={selectedReserve.id}
          open={isClustersDrawerOpen}
          reserveId={selectedReserve.id}
          defaultValues={{
            thermals: Object.keys(thermalCertifications[selectedReserve.id] ?? {}),
          }}
          onClose={() => setIsClustersDrawerOpen(false)}
          onSubmit={handleClustersSubmit}
        />
      )}
      {editingCluster && (
        <UpdateCertificationDrawer
          key={editingCluster.id}
          open={isUpdateDrawerOpen}
          clusterName={editingCluster.name}
          clusterEnabled={editingCluster.enabled}
          certification={editingCluster.certification}
          onClose={() => setIsUpdateDrawerOpen(false)}
          onSubmit={handleCertificationSubmit}
        />
      )}
    </>
  );
}
