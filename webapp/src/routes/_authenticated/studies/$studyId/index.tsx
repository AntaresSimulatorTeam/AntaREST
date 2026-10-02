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

import SimpleLoader from "@/components/loaders/SimpleLoader";
import SplitView from "@/components/page/SplitView";
import { jobQueries } from "@/queries/jobs/queries";
import { variantQueries } from "@/queries/variants/queries";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import InformationView from "./-components/InformationView";
import VariantsTree from "./-components/VariantsTree";
import useStudy from "./-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/")({
  loader: async ({ context, params: { studyId } }) => {
    await context.queryClient.ensureQueryData(jobQueries.list(studyId));
  },
  component: StudyHome,
});

function StudyHome() {
  const study = useStudy();
  const navigate = useNavigate();
  // `isFetching` prevents rendering an outdated tree during background refetches
  const { data: variantTree, isFetching } = useSuspenseQuery(variantQueries.variantTree(study.id));

  return (
    <SplitView splitId="study-home" gutterSize={4} sizes={[30, 70]}>
      {/* Left */}
      {isFetching ? (
        <SimpleLoader />
      ) : (
        <VariantsTree
          variantTree={variantTree}
          onClick={(studyId: string) => navigate({ to: "/studies/$studyId", params: { studyId } })}
        />
      )}
      {/* Right */}
      <InformationView variantTree={variantTree} />
    </SplitView>
  );
}
