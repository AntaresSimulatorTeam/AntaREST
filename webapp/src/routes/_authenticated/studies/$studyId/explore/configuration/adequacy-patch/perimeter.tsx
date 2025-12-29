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

import ViewWrapper from "@/components/page/ViewWrapper";
import TableMode from "@/components/TableMode";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_authenticated/studies/$studyId/explore/configuration/adequacy-patch/perimeter",
)({
  component: Perimeter,
});

function Perimeter() {
  const { studyId } = Route.useParams();

  return (
    <ViewWrapper>
      <TableMode studyId={studyId} type="areas" columns={["adequacyPatchMode"]} />
    </ViewWrapper>
  );
}
