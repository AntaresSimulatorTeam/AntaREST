import { ComponentType, useEffect, useMemo, useState } from "react";
import { Box } from "@mui/material";
import SplitView from "../../../../../../../common/SplitView";
import PropertiesView from "../../../../../../../common/PropertiesView";
import ListElement from "../../../../common/ListElement";
import {
  GenericScenarioConfig,
  HandlerReturnTypes,
  ScenarioType,
  ClustersHandlerReturn,
  getConfigByScenario,
  ScenarioConfig,
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
    "areas" in config &&
    Array.isArray(config.areas) &&
    config.areas.every((area) => typeof area === "string")
  );
}

function withAreas(
  Component: ComponentType<
    ScenarioTableProps & {
      config: GenericScenarioConfig | ClustersHandlerReturn;
    }
  >,
) {
  return function TableWithAreas({
    type,
    config,
    ...props
  }: ScenarioTableProps) {
    const [selectedAreaId, setSelectedAreaId] = useState("");
    const [areas, setAreas] = useState<string[]>([]);
    const [configByArea, setConfigByArea] = useState<
      GenericScenarioConfig | ClustersHandlerReturn
    >({});

    const scenarioConfig = useMemo(
      () => getConfigByScenario(config, type),
      [config, type],
    );

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
      return (
        <Component
          {...props}
          config={scenarioConfig}
          type={type}
          areaId={selectedAreaId}
        />
      );
    }

    return (
      <SplitView direction="horizontal" sizes={[15, 85]} gutterSize={3}>
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
          <Component
            {...props}
            config={configByArea}
            type={type}
            areaId={selectedAreaId}
          />
        </Box>
      </SplitView>
    );
  };
}

export default withAreas;
