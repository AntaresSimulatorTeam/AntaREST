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

import EmptyView from "@/components/page/EmptyView";
import RouterListView from "@/components/page/list/RouterListView";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getAreas } from "@/redux/selectors";
import type { AreaWithId } from "@/types/types";
import { createFileRoute, linkOptions, useParams } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling/areas")({
  component: AreasLayout,
});

function AreasLayout() {
  const navigate = Route.useNavigate();
  const { studyId } = Route.useParams();
  const { areaId, thermalId, storageId, renewableId } = useParams({ strict: false });
  const response = useStudySynthesis({ studyId, selector: getAreas });

  // Redirect to first area if none is selected
  // TODO: Refactor to use `redirect()` in `beforeLoad` (index.tsx) after replacing Redux with Tanstack Query
  useEffect(() => {
    const { data } = response;

    if (!areaId && data && data.length > 0) {
      navigate({
        from: Route.fullPath,
        to: "$areaId",
        params: { areaId: data[0].id },
        replace: true,
      });
    }
  }, [navigate, areaId, response, studyId]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getAreaLinkOptions = (area: AreaWithId) => {
    const params = { studyId, areaId: area.id };

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

    return linkOptions({
      to: areaId ? "." : "/studies/$studyId/explore/modeling/areas/$areaId",
      params,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={response}
      ifFulfilled={(areas) => (
        <RouterListView
          splitId="areas"
          list={areas.map((area) => ({
            id: area.id,
            label: area.name,
            linkOptions: getAreaLinkOptions(area),
          }))}
          emptyListView={<EmptyView title="No areas" />}
        />
      )}
    />
  );
}
