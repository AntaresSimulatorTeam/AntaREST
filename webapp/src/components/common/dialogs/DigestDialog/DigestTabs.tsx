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

import TabsView from "@/components/common/TabsView";
import DigestMatrix from "./DigestMatrix";
import type { DigestData } from "./types";

interface DigestTabsProps {
  matrices: DigestData;
}

function DigestTabs({ matrices }: DigestTabsProps) {
  const tabItems = [
    {
      label: "Area",
      content: () => <DigestMatrix matrix={matrices.area} />,
    },
    {
      label: "Districts",
      content: () => <DigestMatrix matrix={matrices.districts} />,
    },
    {
      label: "Flow Linear",
      content: () => <DigestMatrix matrix={matrices.flowLinear} />,
    },
    {
      label: "Flow Quadratic",
      content: () => <DigestMatrix matrix={matrices.flowQuadratic} />,
    },
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabsView items={tabItems} divider disablePadding />;
}

export default DigestTabs;
