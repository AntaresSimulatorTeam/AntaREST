/* eslint-disable react/jsx-props-no-spreading */
import { useEffect } from "react";
import * as React from "react";
import { styled, SxProps, Theme } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
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
  })
);

interface Props {
  study: StudyMetadata | undefined;
  tabList: Array<{ label: string; path: string }>;
  border?: boolean;
  tabStyle?: "normal" | "withoutBorder";
  sx?: SxProps<Theme>;
}

function TabWrapper(props: Props) {
  const { study, tabList, border, tabStyle, sx } = props;
  const location = useLocation();
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = React.useState(0);

  useEffect(() => {
    const getTabIndex = (): number => {
      const index = tabList.findIndex(
        (tab) => location.pathname.substring(0, tab.path.length) === tab.path
      );

      if (index >= 0) {
        return index;
      }
      return 0;
    };

    if (study) {
      setSelectedTab(getTabIndex);
    }
  }, [location.pathname, study, tabList]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
    navigate(tabList[newValue].path);
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
        sx
      )}
    >
      <StyledTab
        border={border === true}
        tabStyle={tabStyle}
        value={selectedTab}
        onChange={handleChange}
        variant="scrollable"
        sx={{
          width: "98%",
          ...(border === true
            ? { borderBottom: 1, borderColor: "divider" }
            : {}),
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

TabWrapper.defaultProps = {
  border: undefined,
  tabStyle: "normal",
};

export default TabWrapper;
