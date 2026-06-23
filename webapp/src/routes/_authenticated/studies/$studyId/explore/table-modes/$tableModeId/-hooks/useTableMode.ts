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

import { tableModeQueries } from "@/queries/tableMode/queries";
import type { TableMode } from "@/services/api/tablemode/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

function useTableMode() {
  const { tableModeId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/table-modes/$tableModeId/",
  });
  const { t } = useTranslation();

  const getTableMode = useCallback(
    (tableModes: TableMode[]) => {
      return tableModes.find(({ id }) => id === tableModeId);
    },
    [tableModeId],
  );

  const { data: tableMode } = useSuspenseQuery({
    ...tableModeQueries.list(),
    select: getTableMode,
  });

  if (!tableModeId) {
    throw new Error(t("route.noParameter", { param: "bindingConstraintId" }));
  }

  if (!tableMode) {
    throw new Error(t("study.tableModes.detail.notFound", { id: tableModeId }));
  }

  return tableMode;
}

export default useTableMode;
