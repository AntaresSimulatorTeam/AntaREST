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

import type { ProductionType } from "@/services/api/studies/areas/reserves/types";
import { buildKey } from "@/utils/reactUtils";
import { createFileRoute } from "@tanstack/react-router";
import { useState, useTransition } from "react";
import { DEFAULT_PRODUCTION_TYPE } from "../-productionTypes";
import SymmetriesView from "./-components/SymmetriesView";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/reserves/symmetries/",
)({
  component: ReservesSymmetries,
});

function ReservesSymmetries() {
  const params = Route.useParams();
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
      key={buildKey(params, productionType)}
      productionType={productionType}
      isProductionTypePending={isProductionTypePending}
      onProductionTypeChange={handleProductionTypeChange}
    />
  );
}
