import { TabContext, TabList, TabListProps, TabPanel } from "@mui/lab";
import { Box, Button, Tab } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import Rulesets from "./Rulesets";
import Table from "./Table";
import {
  RULESET_PATH,
  getScenarioBuilderConfig,
  ScenarioBuilderConfig,
  SCENARIOS,
} from "./utils";
import { ScenarioBuilderContext } from "./ScenarioBuilderContext";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import {
  editStudy,
  getStudyData,
} from "../../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import { AxiosError } from "axios";
import withAreas from "./withAreas";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
  nbYears: number;
}

// HOC that provides areas menu, for particular cases. (e.g thermals)
const EnhancedTable = withAreas(Table);

function ScenarioBuilderDialog({ study, open, onClose, nbYears }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [config, setConfig] = useState<ScenarioBuilderConfig>({});
  const [activeRuleset, setActiveRuleset] = useState("");
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].type);

  const res = usePromise(async () => {
    try {
      const [config, rulesetId] = await Promise.all([
        // TODO use nbYears and a query param to get the splitted content
        getScenarioBuilderConfig(study.id),
        getStudyData(study.id, RULESET_PATH), // Active ruleset.
      ]);

      setConfig(config);
      setActiveRuleset(rulesetId);
    } catch (error) {
      // TODO test
      setActiveRuleset(activeRuleset);

      enqueueErrorSnackbar(
        "There is no active ruleset or valid configuration available.",
        error as AxiosError,
      );
    }
  }, [study.id, t, enqueueErrorSnackbar]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleActiveRulesetChange = useCallback(
    async (ruleset: string) => {
      setActiveRuleset(ruleset);
      try {
        await editStudy(ruleset, study.id, RULESET_PATH);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.configuration.error.changeActiveRuleset"),
          error as AxiosError,
        );
      }
    },
    [study.id, t, enqueueErrorSnackbar, setActiveRuleset],
  );

  const handleScenarioChange: TabListProps["onChange"] = (_, type) => {
    setSelectedScenario(type);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const scenarioBuilderContext = useMemo(
    () => ({
      config,
      setConfig,
      refreshConfig: res.reload,
      activeRuleset,
      updateRuleset: handleActiveRulesetChange,
      studyId: study.id,
    }),
    [config, res.reload, activeRuleset, handleActiveRulesetChange, study.id],
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
      <UsePromiseCond
        response={res}
        ifResolved={() => (
          <ScenarioBuilderContext.Provider value={scenarioBuilderContext}>
            <Rulesets />
            {activeRuleset && (
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
                {SCENARIOS.map(({ type, symbol }) => (
                  <TabPanel
                    key={type}
                    value={type}
                    sx={{ px: 1, height: 1, overflow: "auto" }}
                  >
                    <EnhancedTable symbol={symbol} />
                  </TabPanel>
                ))}
              </TabContext>
            )}
          </ScenarioBuilderContext.Provider>
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioBuilderDialog;
