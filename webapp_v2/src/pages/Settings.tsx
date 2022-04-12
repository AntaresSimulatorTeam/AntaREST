import SettingsIcon from "@mui/icons-material/Settings";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, styled, Tab, experimental_sx as sx } from "@mui/material";
import { SyntheticEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import RootPage from "../components/common/page/RootPage";

/**
 * Styles
 */

const TabListWrapper = styled(Box)(
  sx({
    width: 1,
    borderBottom: 1,
    borderColor: "divider",
  })
);

/**
 * Component
 */

function Settings() {
  const [tabValue, setTabValue] = useState("1");
  const [t] = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleTabChange = (event: SyntheticEvent, newValue: string) => {
    setTabValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <TabContext value={tabValue}>
      <RootPage
        title={t("main:settings")}
        titleIcon={SettingsIcon}
        headerBottom={
          <TabListWrapper>
            <TabList onChange={handleTabChange}>
              <Tab label={t("settings:users")} value="1" />
              <Tab label={t("settings:groups")} value="2" />
              <Tab label={t("settings:tokens")} value="3" />
              <Tab label={t("settings:maintenance")} value="4" />
            </TabList>
          </TabListWrapper>
        }
        hideHeaderDivider
      >
        <TabPanel value="1" />
        <TabPanel value="2">Groups</TabPanel>
        <TabPanel value="3">Tokens</TabPanel>
        <TabPanel value="4">Maintenance</TabPanel>
      </RootPage>
    </TabContext>
  );
}

export default Settings;
