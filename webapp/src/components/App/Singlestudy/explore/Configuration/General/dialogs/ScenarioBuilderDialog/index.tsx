import { TabContext, TabList, TabListProps, TabPanel } from "@mui/lab";
import { Box, Button, Tab } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { StudyMetadata } from "../../../../../../../../common/types";
import usePromise from "../../../../../../../../hooks/usePromise";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import Rulesets from "./Rulesets";
import Table from "./tabs/Table";
import { getScenarioBuilderConfig } from "./utils";
import ConfigContext from "./ConfigContext";

const TABS_DATA: Array<[string, string]> = [
  ["load", "l"],
  ["thermal", "t"],
  ["hydro", "h"],
  ["wind", "w"],
  ["solar", "s"],
  ["ntc", "ntc"],
  ["hydroLevels", "hl"],
];

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

  usePromise(async () => {
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
              {R.cond<[string], React.ReactNode>([
                [R.equals("thermal"), () => null],
                [R.equals("ntc"), () => null],
                [
                  R.T,
                  () => <Table study={study} nbYears={nbYears} symbol={sym} />,
                ],
              ])(name)}
            </TabPanel>
          ))}
        </TabContext>
      </ConfigContext.Provider>
    </BasicDialog>
  );
}

export default ScenarioBuilderDialog;
