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

import type { Thermal, ThermalParams } from "@/services/api/studies/areas/thermals/types";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useThermals from "../../-hooks/useThermals";

function useThermal({ studyId, areaId, thermalId }: ThermalParams) {
  const { t } = useTranslation();

  const getThermal = useCallback(
    (thermals: Thermal[]) => {
      return thermals.find(({ id }) => id === thermalId);
    },
    [thermalId],
  );

  const { data: thermal } = useThermals({ studyId, areaId, select: getThermal });

  if (!thermalId) {
    throw new Error(t("route.noParameter", { param: "thermalId" }));
  }

  if (!thermal) {
    throw new Error(t("study.modeling.thermals.notFound", { id: thermalId }));
  }

  return thermal;
}

export default useThermal;
