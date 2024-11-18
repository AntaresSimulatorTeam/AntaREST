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
import { StudyMetadata } from "../../../../../../common/types";
import EmptyView from "../../../../../common/page/SimpleContent";
import LinkPropsView from "./LinkPropsView";
import useStudySynthesis from "../../../../../../redux/hooks/useStudySynthesis";
import { getCurrentLink } from "../../../../../../redux/selectors";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import { setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import LinkView from "./LinkView";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import SplitView from "../../../../../common/SplitView";
import ViewWrapper from "../../../../../common/page/ViewWrapper";

function Links() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const res = useStudySynthesis({
    studyId: study.id,
    selector: getCurrentLink,
  });

  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (linkName: string): void => {
    dispatch(setCurrentLink(linkName));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView id="links" sizes={[10, 90]}>
      {/* Left */}
      <LinkPropsView studyId={study.id} onClick={handleLinkClick} />
      {/* Right */}
      <ViewWrapper>
        <UsePromiseCond
          response={res}
          ifFulfilled={(currentLink) =>
            currentLink ? (
              <LinkView link={currentLink} />
            ) : (
              <EmptyView title="No Links" />
            )
          }
        />
      </ViewWrapper>
    </SplitView>
  );
}

export default Links;
