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

import i18n from "@/i18n";
import { reserveKeys } from "@/queries/reserves/keys";
import { storageQueries } from "@/queries/storages/queries";
import { thermalQueries } from "@/queries/thermals/queries";
import { HYDRO_ASSET_ID } from "@/services/api/studies/areas/reserves/constants";
import { productionTypeSchema } from "@/services/api/studies/areas/reserves/schemas";
import type {
  ProductionType,
  ReserveCertification,
  ReserveCertificationField,
  StorageReserveCertification,
  ThermalReserveCertification,
} from "@/services/api/studies/areas/reserves/types";
import type { Study } from "@/services/api/studies/types";
import type { AreaWithId } from "@/types/types";
import { queryOptions, type UseSuspenseQueryOptions } from "@tanstack/react-query";
import type { TFunction } from "i18next";
import StorageCertificationFields from "./-components/certificationFields/StorageCertificationFields";
import ThermalCertificationFields from "./-components/certificationFields/ThermalCertificationFields";

/**
 * An asset that can be certified for a reserve: a thermal cluster, a short-term
 * storage, or the area's hydro. `enabled` is omitted for assets that have no
 * activation state (hydro).
 */
export interface ReserveAsset {
  id: string;
  name: string;
  enabled?: boolean;
}

/**
 * Each asset query fetches its own model under its own key (thermal clusters,
 * storages, ...) and narrows it to `ReserveAsset[]` via `select`: only that
 * selected type matters to consumers. The other generics are `any` so that
 * heterogeneous queries fit one type and `useSuspenseQueries` can infer it.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ReserveAssetsQuery = UseSuspenseQueryOptions<any, any, ReserveAsset[], any>;

/**
 * Everything the certifications and symmetries screens need to know about a
 * production type. Adding a type means adding an entry to `PRODUCTION_TYPES`:
 * the screens themselves are agnostic.
 */
export interface ProductionTypeConfig<
  TCertification extends ReserveCertification = ReserveCertification,
> {
  labelKey: string;
  assetsQuery: (studyId: Study["id"], areaId: AreaWithId["id"]) => ReserveAssetsQuery;
  assetsHaveActivationState: boolean;
  /**
   * Certification parameters, in display order. Each one has a translation at
   * `study.modeling.reserves.certifications.field.<name>`.
   */
  certificationFields: ReadonlyArray<ReserveCertificationField<TCertification>>;
  /** Parameters given to a newly certified asset. */
  defaultCertification: TCertification;
  /**
   * Whether a certification is saved but has no effect yet (e.g. a zero max
   * power): the table then prompts the user to fill it in.
   */
  isCertificationIncomplete: (certification: TCertification) => boolean;
  /** i18n key of the tooltip shown on incomplete certifications. */
  incompleteLabelKey: string;
  /** Form fields editing one certification, rendered inside `UpdateCertificationDrawer`. */
  CertificationFields: React.ComponentType;
}

/**
 * Registers a production type config. The screens look configs up by a runtime
 * `ProductionType` value, so they can only see the union certification type:
 * this is the single place where a type-specific config is widened, on the
 * guarantee that a config is only ever given certifications of its own type.
 *
 * @param config - The type-specific config.
 * @returns The same config, typed against the union certification.
 */
function defineProductionType<TCertification extends ReserveCertification>(
  config: ProductionTypeConfig<TCertification>,
): ProductionTypeConfig {
  return config as unknown as ProductionTypeConfig;
}

const toReserveAsset = ({ id, name, enabled }: ReserveAsset): ReserveAsset => ({
  id,
  name,
  enabled,
});

const THERMAL_CERTIFICATION_FIELDS = [
  "participationCost",
  "participationCostOff",
  "maxPower",
  "maxPowerOff",
] as const satisfies ReadonlyArray<keyof ThermalReserveCertification>;

const STORAGE_CERTIFICATION_FIELDS = [
  "participationCost",
  "maxRelease",
  "maxStore",
] as const satisfies ReadonlyArray<keyof StorageReserveCertification>;

const STORAGE_CONFIG: ProductionTypeConfig<StorageReserveCertification> = {
  labelKey: "study.modeling.reserves.productionType.storages",
  assetsQuery: (studyId, areaId) =>
    queryOptions({
      ...storageQueries.list(studyId, areaId),
      select: (storages) => storages.map(toReserveAsset),
    }),
  assetsHaveActivationState: true,
  certificationFields: STORAGE_CERTIFICATION_FIELDS,
  defaultCertification: { participationCost: 0, maxRelease: 0, maxStore: 0 },
  isCertificationIncomplete: ({ maxRelease, maxStore }) => maxRelease === 0 && maxStore === 0,
  incompleteLabelKey: "study.modeling.reserves.certifications.incomplete.storages",
  CertificationFields: StorageCertificationFields,
};

export const PRODUCTION_TYPES: Record<ProductionType, ProductionTypeConfig> = {
  thermals: defineProductionType<ThermalReserveCertification>({
    labelKey: "study.modeling.reserves.productionType.thermals",
    assetsQuery: (studyId, areaId) =>
      queryOptions({
        ...thermalQueries.list(studyId, areaId),
        select: (clusters) => clusters.map(toReserveAsset),
      }),
    assetsHaveActivationState: true,
    certificationFields: THERMAL_CERTIFICATION_FIELDS,
    defaultCertification: {
      maxPower: 0,
      maxPowerOff: 0,
      participationCost: 0,
      participationCostOff: 0,
    },
    isCertificationIncomplete: ({ maxPower }) => maxPower === 0,
    incompleteLabelKey: "study.modeling.reserves.certifications.incomplete.thermals",
    CertificationFields: ThermalCertificationFields,
  }),
  storages: defineProductionType(STORAGE_CONFIG),
  // Hydro is the area's single long-term storage: same certification model as
  // short-term storages, exposed as one static asset (see `HYDRO_ASSET_ID`).
  hydro: defineProductionType<StorageReserveCertification>({
    ...STORAGE_CONFIG,
    labelKey: "study.modeling.reserves.productionType.hydro",
    assetsQuery: () =>
      queryOptions({
        queryKey: [...reserveKeys.all(), "hydroAsset"],
        queryFn: (): ReserveAsset[] => [
          { id: HYDRO_ASSET_ID, name: i18n.t("study.modeling.hydro") },
        ],
        staleTime: Infinity,
      }),
    assetsHaveActivationState: false,
  }),
};

export const PRODUCTION_TYPE_OPTIONS = productionTypeSchema.options.map((value) => ({
  value,
  label: (t: TFunction) => t(PRODUCTION_TYPES[value].labelKey),
}));

export const DEFAULT_PRODUCTION_TYPE: ProductionType = "thermals";
