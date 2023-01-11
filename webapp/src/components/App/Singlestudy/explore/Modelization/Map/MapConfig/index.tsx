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

      <TabContext value={value}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <TabList onChange={handleChange}>
            <Tab label="Layers" value="layers" />
            <Tab label="Districts" value="districts" />
          </TabList>
        </Box>
        <TabPanel value="layers">
          <Layers />
        </TabPanel>
        <TabPanel value="districts">
          <Districts />
        </TabPanel>
      </TabContext>
    </Box>
  );
}

export default MapConfig;
