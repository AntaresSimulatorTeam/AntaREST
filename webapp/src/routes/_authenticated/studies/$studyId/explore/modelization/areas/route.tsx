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

import EmptyView from "@/components/page/EmptyView";
import ListView from "@/components/page/ListView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getAreas } from "@/redux/selectors";
import { createFileRoute, useMatchRoute } from "@tanstack/react-router";
import { useEffect } from "react";
import useStudy from "../../../../../../-shared/hook/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modelization/areas")(
  {
    component: AreasLayout,
  },
);

function AreasLayout() {
  const study = useStudy();
  const navigate = Route.useNavigate();

  const response = useStudySynthesis({
    studyId: study.id,
    selector: getAreas,
  });

  const matchRoute = useMatchRoute();

  const isAreaSelected = !!matchRoute({
    to: "/studies/$studyId/explore/modelization/areas/$areaId",
    params: { studyId: study.id },
    fuzzy: true,
  });

  // Redirect to first area if none is selected
  useEffect(() => {
    const { data } = response;

    if (!isAreaSelected && data && data.length > 0) {
      navigate({
        to: "/studies/$studyId/explore/modelization/areas/$areaId/properties",
        params: { studyId: study.id, areaId: data[0].id },
        replace: true,
      });
    }
  }, [isAreaSelected, navigate, response, study.id]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // renewablesClustering={renewablesClustering !== "aggregated"}

  return (
    <UsePromiseCond
      response={response}
      ifFulfilled={(areas) => (
        <ListView
          splitId="areas"
          list={areas.map((area) => ({
            ...area,
            label: area.name,
            linkOptions: {
              to: "/studies/$studyId/explore/modelization/areas/$areaId",
              params: { studyId: study.id, areaId: area.id },
            },
          }))}
          emptyListContent={<EmptyView title="No areas" />}
        />
      )}
    />
  );
}
