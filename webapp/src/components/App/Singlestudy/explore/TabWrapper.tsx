/* eslint-disable react/jsx-props-no-spreading */
import { useEffect } from "react";
import * as React from "react";
import { styled } from "@mui/material";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Box from "@mui/material/Box";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { StudyMetadata } from "../../../../common/types";

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
}

function BasicTabs(props: Props) {
  const { study, tabList, border, tabStyle } = props;
  const location = useLocation();
  const navigate = useNavigate();
  const [value, setValue] = React.useState(0);

  useEffect(() => {
    const getDefaultIndex = (): number => {
      const index = tabList.findIndex(
        (elm) => location.pathname.substring(0, elm.path.length) === elm.path
      );
      if (index >= 0) return index;
      return 0;
    };
    if (study) {
      setValue(getDefaultIndex);
    }
  }, [location.pathname, study, tabList]);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
    navigate(tabList[newValue].path);
  };
  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="center"
    >
      <StyledTab
        border={border === true}
        tabStyle={tabStyle}
        value={value}
        onChange={handleChange}
        aria-label="basic tabs example"
        sx={{
          width: "98%",
          ...(border === true
            ? { borderBottom: 1, borderColor: "divider" }
            : {}),
        }}
      >
        {tabList.map((elm) => (
          <Tab key={elm.path} label={elm.label} />
        ))}
      </StyledTab>
      <Outlet context={{ study }} />
    </Box>
  );
}

BasicTabs.defaultProps = {
  border: undefined,
  tabStyle: "normal",
};

export default BasicTabs;
