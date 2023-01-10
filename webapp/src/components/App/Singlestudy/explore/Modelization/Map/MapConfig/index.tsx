import { Box, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import TabWrapper from "../../../TabWrapper";

interface Props {
  onClose: () => void;
}

function MapConfig({ onClose }: Props) {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(
    () => [
      {
        label: "Layers",
        path: `/studies/${study?.id}/explore/modelization/map/layers`,
      },
      {
        label: "Districts",
        path: `/studies/${study?.id}/explore/modelization/map/districts`,
      },
    ],
    [study]
  );

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

      <TabWrapper study={study} tabStyle="normal" tabList={tabList} />
    </Box>
  );
}

export default MapConfig;
