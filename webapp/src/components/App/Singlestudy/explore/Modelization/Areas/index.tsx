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

import { useLocation, useNavigate, useOutletContext } from "react-router";
import { setCurrentArea } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getCurrentArea, getStudySynthesis } from "../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../types/types";
import SplitView from "../../../../../common/SplitView";
import EmptyView from "../../../../../common/page/EmptyView";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";

function Areas() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const res = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudySynthesis(state, id)?.enr_modelling,
  });
  const currentArea = useAppSelector(getCurrentArea);
  const dispatch = useAppDispatch();
  const location = useLocation();
  const navigate = useNavigate();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const updateUrl = (newAreaId: string) => {
    let pathSegments = location.pathname.split("/");
    const areaIndex = pathSegments.findIndex((segment) => segment === "area");
    const areaIdIndex = areaIndex + 1;

    if (areaIndex !== -1 && newAreaId !== pathSegments[areaIdIndex]) {
      const nextPageIndex = areaIdIndex + 1;

      // Set the new area ID
      pathSegments[areaIdIndex] = newAreaId;

      // If the we are in a cluster page, we don't keep the cluster ID
      if (["thermal", "storages", "renewables"].includes(pathSegments[nextPageIndex])) {
        pathSegments = pathSegments.slice(0, nextPageIndex + 1);
      }

      navigate(pathSegments.join("/"), { replace: true });
    }
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaClick = (areaId: string): void => {
    dispatch(setCurrentArea(areaId));
    updateUrl(areaId);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="areas" sizes={[10, 90]}>
      {/* Left */}
      <AreaPropsView studyId={study.id} onClick={handleAreaClick} currentArea={currentArea?.id} />
      {/* Right */}
      <ViewWrapper>
        <UsePromiseCond
          response={res}
          ifFulfilled={(renewablesClustering) =>
            currentArea ? (
              <AreasTab renewablesClustering={renewablesClustering !== "aggregated"} />
            ) : (
              <EmptyView title="No areas" />
            )
          }
        />
      </ViewWrapper>
    </SplitView>
  );
}

export default Areas;
