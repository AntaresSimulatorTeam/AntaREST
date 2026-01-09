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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getArea } from "@/redux/selectors";
import useStudy from "@/routes/-shared/hook/useStudy";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useArea() {
  const study = useStudy();
  const { areaId } = useParams({ strict: false });
  const area = useAppSelector((state) => (areaId ? getArea(state, study.id, areaId) : undefined));
  const { t } = useTranslation();

  if (!areaId) {
    throw new Error(t("route.noParameter", { param: "areaId" }));
  }

  if (!area) {
    throw new Error(t("study.area.notFound", { id: areaId }));
  }

  return area;
}

export default useArea;
