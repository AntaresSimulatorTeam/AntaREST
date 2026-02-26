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
import { getLinks } from "@/redux/selectors";
import { createFileRoute, linkOptions, useParams } from "@tanstack/react-router";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/modeling/links")({
  component: LinksLayout,
});

function LinksLayout() {
  const navigate = Route.useNavigate();
  const { studyId } = Route.useParams();
  const { linkId } = useParams({ strict: false });
  const response = useStudySynthesis({ studyId, selector: getLinks });
  const { t } = useTranslation();

  // Redirect to first link if none is selected
  // TODO: Refactor to use `redirect()` in `beforeLoad` (index.tsx) after replacing Redux with Tanstack Query
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
        <RouterListView
          splitId="links"
          list={links.map((link) => ({
            id: link.id,
            label: link.label,
            linkOptions: linkOptions({
              to: linkId ? "." : "/studies/$studyId/explore/modeling/links/$linkId",
              params: { studyId, linkId: link.id },
            }),
          }))}
          emptyListView={<EmptyView title={t("study.modeling.links.empty")} />}
        />
      )}
    />
  );
}
