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

import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import EmptyView from "../../../../../common/page/EmptyView";
import AreaPropsView from "./AreaPropsView";
import AreasTab from "./AreasTab";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getStudySynthesis, getCurrentArea } from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentArea } from "../../../../../../redux/ducks/studySyntheses";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import SplitView from "../../../../../common/SplitView";
import ViewWrapper from "../../../../../common/page/ViewWrapper";

function Areas() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const res = useStudySynthesis({
    studyId: study.id,
    selector: (state, id) => getStudySynthesis(state, id)?.enr_modelling,
  });
  const currentArea = useAppSelector(getCurrentArea);
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaClick = (areaId: string): void => {
    dispatch(setCurrentArea(areaId));
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
