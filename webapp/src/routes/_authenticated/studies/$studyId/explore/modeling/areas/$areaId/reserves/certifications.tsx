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

import { areaKeys } from "@/queries/areas/keys";
import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type {
  CertificationProductionType,
  Reserve,
  ReserveCertification,
  ReserveCertifications,
} from "@/services/api/studies/areas/reserves/types";
import type { AreaWithId } from "@/types/types";
import { Alert } from "@mui/material";
import { queryOptions, useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Study } from "@/services/api/studies/types";
import { getThermalClusters } from "../thermals/-utils";
import CertificationsTable, {
  type ClusterRow,
  type ReserveRow,
} from "./-components/CertificationsTable";
import EditCertificationDrawer from "./-components/EditCertificationDrawer";
import ReserveClustersDrawer, {
  type ClustersFormValues,
  type ClustersSection,
} from "./-components/ReserveClustersDrawer";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/certifications",
)({
  component: ReservesCertifications,
});

// Thermal clusters have no query layer yet (their API service still lives in the
// thermals route folder), so the query options are defined here for now.
const thermalClustersQueries = {
  list: (studyId: Study["id"], areaId: AreaWithId["id"]) => {
    return queryOptions({
      queryKey: [...areaKeys.all(), "thermals", { studyId, areaId }],
      queryFn: () => getThermalClusters(studyId, areaId),
    });
  },
};

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
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);

  const { data: reservesEnabled } = useSuspenseQuery(reserveQueries.enabled(studyId));

  const { data: reserves, isFetching: isReservesFetching } = useSuspenseQuery(
    reserveQueries.list(studyId, areaId),
  );

  const { data: thermalCertifications } = useSuspenseQuery(
    reserveQueries.certifications(studyId, areaId, "thermals"),
  );

  const { data: thermalClusters } = useSuspenseQuery(thermalClustersQueries.list(studyId, areaId));

  // Certifications mapping per production type. "storages" and "hydro" will be
  // added once their endpoints are released.
  const certificationsByType: Record<CertificationProductionType, ReserveCertifications> = {
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
    const clusterNamesById = new Map(thermalClusters.map(({ id, name }) => [id, name]));

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
          name: clusterNamesById.get(clusterId) ?? clusterId,
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
    setIsEditDrawerOpen(true);
  };

  // Rebuilds each production type's mapping from the selection: kept clusters
  // retain their parameters, new ones get the defaults, deselected ones are
  // removed (the PUT endpoint replaces the whole mapping).
  const handleClustersSubmit = async (values: ClustersFormValues) => {
    if (!selectedReserve) {
      return;
    }

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

      await updateMutation.mutateAsync({ studyId, areaId, productionType, data });
    }
  };

  const handleCertificationSubmit = async (certification: ReserveCertification) => {
    if (!editingCluster) {
      return;
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

    await updateMutation.mutateAsync({ studyId, areaId, productionType, data });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const sections: ClustersSection[] = selectedReserve
    ? [
        {
          productionType: "thermals",
          label: t("study.modeling.reserves.certifications.productionType.thermals"),
          clusters: thermalClusters,
          certifiedIds: Object.keys(thermalCertifications[selectedReserve.id] ?? {}),
        },
        // "storages" and "hydro" sections will be added once their endpoints are released
      ]
    : [];

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
        <ReserveClustersDrawer
          key={selectedReserve.id}
          open={isClustersDrawerOpen}
          title={selectedReserve.name}
          sections={sections}
          onClose={() => setIsClustersDrawerOpen(false)}
          onSubmit={handleClustersSubmit}
        />
      )}
      {editingCluster && (
        <EditCertificationDrawer
          key={editingCluster.id}
          open={isEditDrawerOpen}
          clusterName={editingCluster.name}
          certification={editingCluster.certification}
          onClose={() => setIsEditDrawerOpen(false)}
          onSubmit={handleCertificationSubmit}
        />
      )}
    </>
  );
}
