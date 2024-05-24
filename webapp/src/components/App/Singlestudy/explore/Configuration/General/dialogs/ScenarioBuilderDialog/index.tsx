import { TabContext, TabList, TabListProps, TabPanel } from "@mui/lab";
import { Box, Button, Tab, Skeleton } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import Table from "./Table";
import {
  getScenarioConfigByType,
  ScenarioBuilderConfig,
  SCENARIOS,
  ScenarioType,
} from "./utils";
import { ScenarioBuilderContext } from "./ScenarioBuilderContext";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { AxiosError } from "axios";
import withAreas from "./withAreas";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

// HOC that provides areas menu, for particular cases. (e.g thermals)
const EnhancedTable = withAreas(Table);

function ScenarioBuilderDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [config, setConfig] = useState<ScenarioBuilderConfig>({});
  const [selectedScenario, setSelectedScenario] = useState<ScenarioType>(
    SCENARIOS[0].type,
  );

  const scenarioConfig = usePromise(async () => {
    try {
      const config = await getScenarioConfigByType(study.id, selectedScenario);
      setConfig(config);
    } catch (error) {
      enqueueErrorSnackbar(
        "There is no active ruleset or valid configuration available.",
        error as AxiosError,
      );
    }
  }, [study.id, t, enqueueErrorSnackbar]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleScenarioChange: TabListProps["onChange"] = (_, type) => {
    try {
      setSelectedScenario(type);
      scenarioConfig.reload();
    } catch (error) {
      enqueueErrorSnackbar(
        "Failed to fetch configuration for the selected scenario.",
        error as AxiosError,
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  console.log("scenarioConfig.isLoading", scenarioConfig.isLoading);

  const scenarioBuilderContext = useMemo(
    () => ({
      config,
      setConfig,
      refreshConfig: scenarioConfig.reload,
      isConfigLoading: scenarioConfig.isLoading,
      studyId: study.id,
    }),
    [config, scenarioConfig.isLoading, scenarioConfig.reload, study.id],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.configuration.general.mcScenarioBuilder")}
      open={open}
      onClose={onClose}
      actions={<Button onClick={onClose}>{t("button.close")}</Button>}
      maxWidth="xl"
      fullWidth
      contentProps={{
        sx: { p: 1, height: "95vh", width: 1 },
      }}
    >
      <ScenarioBuilderContext.Provider value={scenarioBuilderContext}>
        <TabContext value={selectedScenario}>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <TabList onChange={handleScenarioChange}>
              {SCENARIOS.map(({ type }) => (
                <Tab
                  key={type}
                  value={type}
                  label={t(
                    `study.configuration.general.mcScenarioBuilder.tab.${type}`,
                  )}
                />
              ))}
            </TabList>
          </Box>
          {SCENARIOS.map(({ type }) => (
            <TabPanel
              key={type}
              value={type}
              sx={{ px: 1, height: 1, overflow: "auto" }}
            >
              <UsePromiseCond
                response={scenarioConfig}
                ifResolved={() => <EnhancedTable type={type} />}
                ifPending={() => (
                  <Skeleton sx={{ height: 1, transform: "none" }} />
                )}
              />
            </TabPanel>
          ))}
        </TabContext>
      </ScenarioBuilderContext.Provider>
    </BasicDialog>
  );
}
export default ScenarioBuilderDialog;
