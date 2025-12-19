/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

function useArea() {
  const study = useStudy();

  const { areaId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId",
  });

  const area = useAppSelector((state) => getArea(state, study.id, areaId));

  if (!area) {
    throw new Error(`No area found with ID: ${areaId}`);
  }

  return area;
}

export default useArea;
