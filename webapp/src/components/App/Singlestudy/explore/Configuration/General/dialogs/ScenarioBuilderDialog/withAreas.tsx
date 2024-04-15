import {
  ComponentType,
  ReactElement,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Box } from "@mui/material";
import SplitView from "../../../../../../../common/SplitView";
import PropertiesView from "../../../../../../../common/PropertiesView";
import ListElement from "../../../../common/ListElement";
import {
  GenericScenarioConfig,
  HandlerReturnTypes,
  ScenarioSymbol,
  ThermalHandlerReturn,
  getConfigByScenario,
} from "./utils";
import { ScenarioBuilderContext } from "./ScenarioBuilderContext";

interface ScenarioTableProps {
  symbol: ScenarioSymbol;
  areaId?: string;
}

function hasAreas(
  config: HandlerReturnTypes[keyof HandlerReturnTypes],
): config is ThermalHandlerReturn {
  // TODO make a generic type for areas configurations return
  return (
    "areas" in config &&
    Array.isArray(config.areas) &&
    config.areas.every((area) => typeof area === "string")
  );
}

function withAreas(
  Component: ComponentType<
    ScenarioTableProps & {
      config: GenericScenarioConfig | ThermalHandlerReturn;
    }
  >,
) {
  return function TableWithAreas({
    symbol,
    ...props
  }: ScenarioTableProps): ReactElement {
    const { config, activeRuleset } = useContext(ScenarioBuilderContext);
    const [selectedAreaId, setSelectedAreaId] = useState("");
    const [areas, setAreas] = useState<string[]>([]);
    const [configByArea, setConfigByArea] = useState<
      GenericScenarioConfig | ThermalHandlerReturn
    >({});

    const scenarioConfig = useMemo(
      () => getConfigByScenario(config, activeRuleset, symbol),
      [config, activeRuleset, symbol],
    );

    console.log("scenarioConfig", scenarioConfig);

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

    console.log("selectedAreaId", selectedAreaId);
    console.log("symbol", symbol);
    console.log("configByArea", configByArea);

    ////////////////////////////////////////////////////////////////
    // JSX
    ////////////////////////////////////////////////////////////////

    // The regular case where no nested data depending on areas.
    if (!areas.length && scenarioConfig) {
      return (
        <Component
          {...props}
          config={scenarioConfig}
          symbol={symbol}
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
            symbol={symbol}
            areaId={selectedAreaId}
          />
        </Box>
      </SplitView>
    );
  };
}

export default withAreas;
