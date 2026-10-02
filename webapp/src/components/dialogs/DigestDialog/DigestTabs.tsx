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

import TabsView from "@/components/page/TabsView";
import DigestMatrix from "./DigestMatrix";
import type { DigestData } from "./types";

interface DigestTabsProps {
  matrices: DigestData;
}

function DigestTabs({ matrices }: DigestTabsProps) {
  const tabItems = [
    {
      id: "area",
      label: "Area",
      content: <DigestMatrix matrix={matrices.area} />,
    },
    {
      id: "districts",
      label: "Districts",
      content: <DigestMatrix matrix={matrices.districts} />,
    },
    {
      id: "flow-linear",
      label: "Flow Linear",
      content: <DigestMatrix matrix={matrices.flowLinear} />,
    },
    {
      id: "flow-quadratic",
      label: "Flow Quadratic",
      content: <DigestMatrix matrix={matrices.flowQuadratic} />,
    },
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabsView tabs={tabItems} divider disablePadding />;
}

export default DigestTabs;
