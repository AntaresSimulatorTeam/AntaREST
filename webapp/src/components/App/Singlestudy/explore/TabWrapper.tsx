import { useEffect, useState } from "react";
import * as React from "react";
import { styled, SxProps, Theme } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { Outlet, matchPath, useLocation, useNavigate } from "react-router-dom";
import { StudyMetadata } from "../../../../common/types";
import { mergeSxProp } from "../../../../utils/muiUtils";

export const StyledTab = styled(Tabs, {
  shouldForwardProp: (prop) => prop !== "border" && prop !== "tabStyle",
})<{ border?: boolean; tabStyle?: "normal" | "withoutBorder" }>(
  ({ theme, border, tabStyle }) => ({
    width: "98%",
    height: "50px",
    ...(border === true && {
      borderBottom: 1,
      borderColor: "divider",
    }),
    ...(tabStyle &&
      tabStyle === "withoutBorder" && {
        "& .MuiTabs-indicator": {
          display: "none",
        },
      }),
  }),
);

interface TabItem {
  label: string;
  path: string;
  onClick?: () => void;
}

interface Props {
  study: StudyMetadata | undefined;
  tabList: TabItem[];
  border?: boolean;
  tabStyle?: "normal" | "withoutBorder";
  sx?: SxProps<Theme>;
  isScrollable?: boolean;
}

function TabWrapper({
  study,
  tabList,
  border,
  tabStyle,
  sx,
  isScrollable = false,
}: Props) {
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState(0);

  useEffect(() => {
    const matchedTab = tabList.findIndex((tab) =>
      matchPath({ path: tab.path, end: false }, location.pathname),
    );
    setSelectedTab(matchedTab >= 0 ? matchedTab : 0);
  }, [location.pathname, tabList]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    navigate(tabList[newValue].path);
    tabList[newValue].onClick?.();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={mergeSxProp(
        {
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          alignItems: "center",
        },
        sx,
      )}
    >
      <StyledTab
        border={border}
        tabStyle={tabStyle}
        value={selectedTab}
        onChange={handleChange}
        variant={isScrollable ? "scrollable" : "standard"}
        sx={{
          width: "98%",
          borderBottom: border ? 1 : 0,
          borderColor: border ? "divider" : "inherit",
        }}
      >
        {tabList.map((tab) => (
          <Tab key={tab.path} label={tab.label} />
        ))}
      </StyledTab>
      <Outlet context={{ study }} />
    </Box>
  );
}

export default TabWrapper;
