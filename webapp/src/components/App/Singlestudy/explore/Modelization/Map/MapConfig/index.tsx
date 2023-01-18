import { Box, Button, Tab } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import Layers from "./Layers";
import Districts from "./Districts";

interface Props {
  onClose: () => void;
}

function MapConfig({ onClose }: Props) {
  const [t] = useTranslation();
  const [value, setValue] = useState("layers");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Button
        color="secondary"
        size="small"
        onClick={onClose}
        startIcon={<ArrowBackIcon color="secondary" />}
        sx={{ alignSelf: "flex-start" }}
      >
        {t("button.back")}
      </Button>
      <Box
        sx={{
          flexGrow: 1,
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <TabContext value={value}>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <TabList onChange={handleChange}>
              <Tab label="Layers" value="layers" />
              <Tab label="Districts" value="districts" />
            </TabList>
          </Box>
          <TabPanel
            value="layers"
            sx={{ p: 0, pt: 2, flexGrow: 1, overflow: "hidden" }}
          >
            <Layers />
          </TabPanel>
          <TabPanel
            value="districts"
            sx={{ p: 0, pt: 2, flexGrow: 1, overflow: "hidden" }}
          >
            <Districts />
          </TabPanel>
        </TabContext>
      </Box>
    </Box>
  );
}

export default MapConfig;
