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

import { useEffect, useMemo, useState } from "react";
import { Box } from "@mui/material";
import SplitView from "../../../../../../../common/SplitView";
import PropertiesView from "../../../../../../../common/PropertiesView";
import ListElement from "../../../../common/ListElement";
import {
  getConfigByScenario,
  type GenericScenarioConfig,
  type HandlerReturnTypes,
  type ScenarioType,
  type ClustersHandlerReturn,
  type ScenarioConfig,
} from "./utils";

interface ScenarioTableProps {
  type: ScenarioType;
  config: ScenarioConfig;
  areaId?: string;
}

// If the configuration contains areas/clusters.
function hasAreas(
  config: HandlerReturnTypes[keyof HandlerReturnTypes],
): config is ClustersHandlerReturn {
  return (
    config !== undefined &&
    "areas" in config &&
    Array.isArray(config.areas) &&
    config.areas.every((area) => typeof area === "string")
  );
}

function withAreas(
  Component: React.ComponentType<
    ScenarioTableProps & {
      config: GenericScenarioConfig | ClustersHandlerReturn;
    }
  >,
) {
  return function TableWithAreas({ type, config, ...props }: ScenarioTableProps) {
    const [selectedAreaId, setSelectedAreaId] = useState("");
    const [areas, setAreas] = useState<string[]>([]);
    const [configByArea, setConfigByArea] = useState<GenericScenarioConfig | ClustersHandlerReturn>(
      {},
    );

    const scenarioConfig = useMemo(() => getConfigByScenario(config, type), [config, type]);

    useEffect(() => {
      if (scenarioConfig && hasAreas(scenarioConfig)) {
        setAreas(scenarioConfig.areas);

        // Set selected area ID only if it hasn't been selected yet or current selection is not valid anymore.
        if (!selectedAreaId || !scenarioConfig.areas.includes(selectedAreaId)) {
          setSelectedAreaId(scenarioConfig.areas[0]);
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [scenarioConfig]);

    useEffect(() => {
      if (scenarioConfig && hasAreas(scenarioConfig) && selectedAreaId) {
        setConfigByArea(scenarioConfig.clusters[selectedAreaId]);
      }
    }, [selectedAreaId, scenarioConfig]);

    ////////////////////////////////////////////////////////////////
    // JSX
    ////////////////////////////////////////////////////////////////

    // The regular case where no clusters nested data.
    if (!areas.length && scenarioConfig) {
      return <Component {...props} config={scenarioConfig} type={type} areaId={selectedAreaId} />;
    }

    return (
      <SplitView id="scenario-builder" sizes={[15, 85]}>
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
