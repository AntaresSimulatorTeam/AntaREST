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
import type { AreaWithId } from "@/types/types";
import { createFileRoute, linkOptions, useParams } from "@tanstack/react-router";
import { useEffect } from "react";
import useStudy from "../../../../../../-shared/hook/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling/areas")({
  component: AreasLayout,
});

function AreasLayout() {
  const study = useStudy();
  const navigate = Route.useNavigate();
  const { areaId, thermalId, storageId, renewableId } = useParams({ strict: false });

  const response = useStudySynthesis({
    studyId: study.id,
    selector: getAreas,
  });

  // Redirect to first area if none is selected
  useEffect(() => {
    const { data } = response;

    if (!areaId && data && data.length > 0) {
      navigate({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/properties",
        params: { studyId: study.id, areaId: data[0].id },
        replace: true,
      });
    }
  }, [navigate, areaId, response, study.id]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getAreaLinkOptions = (area: AreaWithId) => {
    const params = { studyId: study.id, areaId: area.id };

    if (thermalId) {
      return linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/thermals",
        params,
      });
    }

    if (storageId) {
      return linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages",
        params,
      });
    }

    if (renewableId) {
      return linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/renewables",
        params,
      });
    }

    if (!areaId) {
      return linkOptions({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/properties",
        params,
      });
    }

    // Keep the current sub-route when switching area
    return linkOptions({ to: ".", params });
  };

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
            linkOptions: getAreaLinkOptions(area),
          }))}
          emptyListContent={<EmptyView title="No areas" />}
        />
      )}
    />
  );
}
