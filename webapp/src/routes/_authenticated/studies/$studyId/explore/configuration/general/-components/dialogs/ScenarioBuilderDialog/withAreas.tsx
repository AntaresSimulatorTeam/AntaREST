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

import PropertiesView from "@/components/PropertiesView";
import SplitView from "@/components/page/SplitView";
import type {
  Level1Display,
  ScenarioDisplay,
  ScenarioType,
} from "@/services/api/studies/config/scenarioBuilder/types";
import { Box } from "@mui/material";
import { useEffect, useState } from "react";
import ListElement from "../../../../../../../../../../components/ListElement";
import { hasAreaSelection, isLevel1Display, isLevel2Display, isLevel3Display } from "./types";
import { requiresAreaSelection } from "./utils";

interface ScenarioTableProps {
  type: ScenarioType;
  config: ScenarioDisplay;
  areaId?: string;
}

function withAreas(
  Component: React.ComponentType<{
    type: ScenarioType;
    config: Level1Display;
    areaId?: string;
  }>,
) {
  return function TableWithAreas({ type, config, ...props }: ScenarioTableProps) {
    const [selectedAreaId, setSelectedAreaId] = useState("");
    const [areas, setAreas] = useState<string[]>([]);
    const [configByArea, setConfigByArea] = useState<Level1Display>({});

    useEffect(() => {
      if (config && hasAreaSelection(config)) {
        setAreas(config.areas);

        // Set selected area ID only if it hasn't been selected yet or current selection is not valid anymore.
        if (!selectedAreaId || !config.areas.includes(selectedAreaId)) {
          setSelectedAreaId(config.areas[0]);
        }
      }
    }, [config, selectedAreaId]);

    useEffect(() => {
      if (config && hasAreaSelection(config) && selectedAreaId) {
        if (isLevel2Display(config)) {
          setConfigByArea(config.entities[selectedAreaId]);
        } else if (isLevel3Display(config)) {
          setConfigByArea(config.flattenedEntities[selectedAreaId]);
        }
      }
    }, [selectedAreaId, config]);

    ////////////////////////////////////////////////////////////////
    // JSX
    ////////////////////////////////////////////////////////////////

    // Handle Level 1 scenarios (no area selection needed)
    if (!requiresAreaSelection(type) && config && isLevel1Display(config)) {
      return <Component {...props} config={config} type={type} />;
    }

    return (
      <SplitView splitId="scenario-builder">
        <PropertiesView
          sx={{ p: 1, ".SearchFE": { mx: 0 } }}
          mainContent={
            <ListElement
              sx={{ p: 0 }}
              list={areas.map((areaId) => ({
                id: areaId,
                name: `${areaId}`,
              }))}
              currentElement={selectedAreaId}
              currentElementKeyToTest="id"
              setSelectedItem={({ id }) => setSelectedAreaId(id)}
            />
          }
        />
        <Box sx={{ p: 1 }}>
          <Component {...props} config={configByArea} type={type} areaId={selectedAreaId} />
        </Box>
      </SplitView>
    );
  };
}

export default withAreas;
