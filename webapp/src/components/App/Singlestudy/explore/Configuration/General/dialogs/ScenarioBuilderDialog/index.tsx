import { TabContext, TabList, TabListProps, TabPanel } from "@mui/lab";
import { Box, Button, Tab } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import Rulesets from "./Rulesets";
import Table from "./tabs/Table";
import { getScenarioBuilderConfig, TABS_DATA } from "./utils";
import ConfigContext from "./ConfigContext";
import Thermal from "./tabs/Thermal";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
  nbYears: number;
}

function ScenarioBuilderDialog(props: Props) {
  const { study, open, onClose, nbYears } = props;
  const [currentTab, setCurrentTab] = useState(TABS_DATA[0][0]);
  const [currentRuleset, setCurrentRuleset] = useState("");
  const [config, setConfig] = useState({});
  const { t } = useTranslation();

  const res = usePromise(async () => {
    const config = await getScenarioBuilderConfig(study.id);
    setConfig(config);
    setCurrentRuleset(Object.keys(config)[0] || "");
  }, [study.id]);

  const cxValue = useMemo(
    () => ({ config, currentRuleset, setCurrentRuleset }),
    [config, currentRuleset]
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange: TabListProps["onChange"] = (_, newValue) => {
    setCurrentTab(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.configuration.general.mcScenarioBuilder")}
      open={open}
      onClose={onClose}
      actions={<Button onClick={onClose}>{t("button.close")}</Button>}
      maxWidth="md"
      fullWidth
      PaperProps={{
        // TODO: add `maxHeight` and `fullHeight` in BasicDialog`
        sx: { height: "calc(100% - 64px)", maxHeight: "900px" },
      }}
    >
      <UsePromiseCond
        response={res}
        ifResolved={() => (
          <ConfigContext.Provider value={cxValue}>
            <Rulesets />
            <TabContext value={currentTab}>
              <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <TabList onChange={handleTabChange}>
                  {TABS_DATA.map(([name]) => (
                    <Tab
                      key={name}
                      value={name}
                      label={t(
                        `study.configuration.general.mcScenarioBuilder.tab.${name}`
                      )}
                    />
                  ))}
                </TabList>
              </Box>
              {TABS_DATA.map(([name, sym]) => (
                <TabPanel
                  key={name}
                  value={name}
                  sx={{ p: 0, pt: 2, height: 1, overflow: "auto" }}
                >
                  {name === "thermal" ? (
                    <Thermal study={study} nbYears={nbYears} />
                  ) : (
                    <Table
                      study={study}
                      nbYears={nbYears}
                      symbol={sym}
                      rowType={name === "ntc" ? "link" : "area"}
                    />
                  )}
                </TabPanel>
              ))}
            </TabContext>
          </ConfigContext.Provider>
        )}
      />
    </BasicDialog>
  );
}

export default ScenarioBuilderDialog;
