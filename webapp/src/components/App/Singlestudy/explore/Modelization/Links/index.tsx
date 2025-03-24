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

import ViewWrapper from "@/components/common/page/ViewWrapper";
import { getLinks } from "@/services/api/studies/links";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import usePromise from "../../../../../../hooks/usePromise";
import { setCurrentLink } from "../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLink } from "../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../types/types";
import EmptyView from "../../../../../common/page/EmptyView";
import SplitView from "../../../../../common/SplitView";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import LinkConfig from "./LinkConfig";
import LinkPropsView from "./LinkPropsView";

function Links() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const currentLink = useAppSelector((state) => getCurrentLink(state, study.id));

  const linksRes = usePromise(() => getLinks({ studyId: study.id }), [study.id]);

  // Handle automatic selection of the first link
  useEffect(() => {
    const { data } = linksRes;

    if (!data || data.length === 0 || currentLink) {
      return;
    }

    dispatch(setCurrentLink(data[0].id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [linksRes.data, currentLink, dispatch]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLinkClick = (linkId: string) => {
    dispatch(setCurrentLink(linkId));
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
          response={linksRes}
          ifFulfilled={(data) =>
            data.length > 0 && currentLink ? (
              <LinkConfig link={currentLink} />
            ) : (
              <EmptyView title={t("study.modelization.links.empty")} />
            )
          }
        />
      </ViewWrapper>
    </SplitView>
  );
}

export default Links;
