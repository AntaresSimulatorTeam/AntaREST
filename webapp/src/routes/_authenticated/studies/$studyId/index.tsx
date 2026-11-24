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

import SplitView from "@/components/page/SplitView";
import { jobQueries } from "@/queries/jobs/queries";
import { createFileRoute } from "@tanstack/react-router";
import InformationView from "./-components/InformationView";
import VariantsTree from "./-components/VariantsTree";

export const Route = createFileRoute("/_authenticated/studies/$studyId/")({
  loader: async ({ context, params: { studyId } }) => {
    await context.queryClient.ensureQueryData(jobQueries.list(studyId));
  },
  component: StudyHome,
});

function StudyHome() {
  return (
    <SplitView splitId="study-home" gutterSize={4} sizes={[30, 70]}>
      {/* Left */}
      <VariantsTree />
      {/* Right */}
      <InformationView />
    </SplitView>
  );
}
