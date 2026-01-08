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
import { getLinks } from "@/redux/selectors";
import { createFileRoute, linkOptions, useParams } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling/links")({
  component: LinksLayout,
});

function LinksLayout() {
  const navigate = Route.useNavigate();
  const { studyId } = Route.useParams();
  const { linkId } = useParams({ strict: false });
  const response = useStudySynthesis({ studyId, selector: getLinks });

  // Redirect to first link if none is selected
  useEffect(() => {
    const { data } = response;

    if (!linkId && data && data.length > 0) {
      navigate({
        from: Route.fullPath,
        to: "$linkId",
        params: { linkId: data[0].id },
        replace: true,
      });
    }
  }, [navigate, linkId, response, studyId]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={response}
      ifFulfilled={(links) => (
        <ListView
          splitId="links"
          list={links.map((link) => ({
            id: link.id,
            label: link.label,
            linkOptions: linkOptions({
              to: "/studies/$studyId/explore/modeling/links/$linkId",
              params: { studyId, linkId: link.id },
            }),
          }))}
          emptyListContent={<EmptyView title="No links" />}
        />
      )}
    />
    // <SplitView splitId="links">
    //   {/* Left */}
    //   <LinkPropsView studyId={study.id} onClick={handleLinkClick} />
    //   {/* Right */}
    //   <ViewWrapper>
    //     <UsePromiseCond
    //       response={linksRes}
    //       ifFulfilled={(data) =>
    //         data.length > 0 && currentLink ? (
    //           <LinkConfig link={currentLink} />
    //         ) : (
    //           <EmptyView title={t("study.modeling.links.empty")} />
    //         )
    //       }
    //     />
    //   </ViewWrapper>
    // </SplitView>
  );
}
