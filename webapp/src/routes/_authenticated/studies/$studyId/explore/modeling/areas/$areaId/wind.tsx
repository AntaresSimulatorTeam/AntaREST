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

import Matrix from "@/components/Matrix";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudySynthesis } from "@/redux/selectors";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/wind",
)({
  component: Wind,
});

function Wind() {
  const { studyId, areaId } = Route.useParams();
  const url = `input/wind/series/wind_${areaId}`;
  const enrModelling = useAppSelector((state) => getStudySynthesis(state, studyId)?.enr_modelling);

  if (enrModelling !== "aggregated") {
    throw new Error(`${Route.path} is only available when 'enr_modelling' is of type aggregated.`);
  }

  return <Matrix key={areaId} studyId={studyId} url={url} aggregateColumns="stats" />;
}
