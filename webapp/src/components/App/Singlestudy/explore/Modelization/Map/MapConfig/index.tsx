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
        label: "Districts",
        path: `/studies/${study?.id}/explore/modelization/map/districts`,
      },
      {
        label: "Layers",
        path: `/studies/${study?.id}/explore/modelization/map/layers`,
      },
    ],
    [study]
  );

  return (
    <Box sx={{ display: "flex", flex: 1, flexDirection: "column" }}>
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
