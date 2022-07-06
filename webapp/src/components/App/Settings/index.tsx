import SettingsIcon from "@mui/icons-material/Settings";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import { Box, Tab } from "@mui/material";
import { SyntheticEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import RootPage from "../../common/page/RootPage";
import Groups from "./Groups";
import Maintenance from "./Maintenance";
import Tokens from "./Tokens";
import Users from "./Users";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import {
  isAuthUserAdmin,
  isAuthUserInGroupAdmin,
} from "../../../redux/selectors";

/**
 * Component
 */

function Settings() {
  const [tabValue, setTabValue] = useState("1");
  const [t] = useTranslation();
  const isUserAdmin = useAppSelector(isAuthUserAdmin);
  const isUserInGroupAdmin = useAppSelector(isAuthUserInGroupAdmin);

  const tabList = useMemo(() => {
    return [
      isUserAdmin && [t("global.users"), () => <Users />],
      (isUserAdmin || isUserInGroupAdmin) && [
        t("global.group"),
        () => <Groups />,
      ],
      [t("global.tokens"), () => <Tokens />],
      isUserAdmin && [t("global.maintenance"), () => <Maintenance />],
    ].filter(Boolean) as Array<[string, () => JSX.Element]>;
  }, [isUserAdmin, isUserInGroupAdmin, t]);

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
        title={t("global.settings")}
        titleIcon={SettingsIcon}
        headerBottom={
          <Box
            sx={{
              width: 1,
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            <TabList onChange={handleTabChange}>
              {tabList.map(([label], index) => (
                <Tab key={label} label={label} value={String(index + 1)} />
              ))}
            </TabList>
          </Box>
        }
        hideHeaderDivider
      >
        {tabList.map(([label, Element], index) => (
          <TabPanel
            sx={{
              paddingTop: 0,
              paddingBottom: 0,
              overflow: "auto",
            }}
            key={label}
            value={String(index + 1)}
          >
            <Element />
          </TabPanel>
        ))}
      </RootPage>
    </TabContext>
  );
}

export default Settings;
