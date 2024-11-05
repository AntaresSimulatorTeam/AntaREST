/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { StudyMetadata } from "@/common/types";
import EmptyView from "@/components/common/page/SimpleContent";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import SplitView from "@/components/common/SplitView";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import { setCurrentArea } from "@/redux/ducks/studySyntheses";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import useStudySynthesis from "@/redux/hooks/useStudySynthesis";
import { getCurrentArea, getStudySynthesis } from "@/redux/selectors";

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
      <AreaPropsView
        studyId={study.id}
        onClick={handleAreaClick}
        currentArea={currentArea?.id}
      />
      {/* Right */}
      <ViewWrapper>
        <UsePromiseCond
          response={res}
          ifResolved={(renewablesClustering) =>
            currentArea ? (
              <AreasTab
                renewablesClustering={renewablesClustering !== "aggregated"}
              />
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
