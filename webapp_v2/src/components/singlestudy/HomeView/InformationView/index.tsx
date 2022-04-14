import { useState } from "react";
import { Paper, Button, Box, Divider } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { StudyMetadata, VariantTree } from "../../../../common/types";
import CreateVariantModal from "./CreateVariantModal";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";
import LauncherModal from "../../../studies/LauncherModal";

interface Props {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
  tree: VariantTree | undefined;
}

function InformationView(props: Props) {
  const { study, tree } = props;
  const navigate = useNavigate();
  const [t] = useTranslation();
  const [openVariantModal, setOpenVariantModal] = useState<boolean>(false);
  const [openLauncherModal, setOpenLauncherModal] = useState<boolean>(false);

  return (
    <Paper
      sx={{
        width: "80%",
        minWidth: "400px",
        height: "90%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        px: 2,
        py: 1,
      }}
    >
      <Box
        width="100%"
        flex={1}
        display="flex"
        flexDirection="row"
        justifyContent="center"
        alignItems="center"
        py={1}
      >
        <LauncherHistory study={study} />
        <Notes study={study} />
      </Box>
      <Divider sx={{ width: "98%", height: "1px" }} />
      <Box
        width="100%"
        flex="0 0 50px"
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <Box
          height="100%"
          display="flex"
          flexDirection="row"
          justifyContent="flex-start"
          alignItems="center"
        >
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              if (study) navigate(`/studies/${study.id}/explore`);
            }}
          >
            {t("main:open")}
          </Button>
          <Button
            variant="text"
            color="primary"
            onClick={() => setOpenVariantModal(true)}
            sx={{ mx: 2 }}
          >
            {t("variants:createNewVariant")}
          </Button>
        </Box>
        <Button
          variant="contained"
          color="primary"
          onClick={() => setOpenLauncherModal(true)}
        >
          {t("main:launch")}
        </Button>
      </Box>
      {study && tree && openVariantModal && (
        <CreateVariantModal
          open={openVariantModal}
          onClose={() => setOpenVariantModal(false)}
          tree={tree}
          parentId={study.id}
        />
      )}
      {openLauncherModal && (
        <LauncherModal
          open={openLauncherModal}
          study={study}
          onClose={() => setOpenLauncherModal(false)}
        />
      )}
    </Paper>
  );
}

export default InformationView;
