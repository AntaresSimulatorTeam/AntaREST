import { useState } from "react";
import { Paper, Button, Box, Divider } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { StudyMetadata, VariantTree } from "../../../../common/types";
import CreateVariantModal from "./CreateVariantModal";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";
import LauncherModal from "../../../studies/LauncherDialog";
import { copyStudy } from "../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";

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
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const importStudy = async (study: StudyMetadata) => {
    try {
      await copyStudy(study.id, `${study.name} (${t("global:global.copy)})`, false);
    } catch (e) {
      enqueueErrorSnackbar(t("studymanager:failtocopystudy"), e as AxiosError);
    }
  };

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
        height="calc(100% - 40px)"
        display="flex"
        flexDirection="row"
        justifyContent="center"
        alignItems="center"
        py={1.5}
      >
        <LauncherHistory study={study} />
        <Notes study={study} />
      </Box>
      <Divider sx={{ width: "100%", height: "1px" }} />
      <Box
        width="100%"
        flex="0 0 40px"
        display="flex"
        flexDirection="row"
        justifyContent="space-between"
        alignItems="flex-start"
        py={1.5}
      >
        <Box
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
          {study && (
            <Button
              variant="text"
              color="primary"
              onClick={() =>
                study.managed ? setOpenVariantModal(true) : importStudy(study)
              }
              sx={{ mx: 2 }}
            >
              {study.managed
                ? t("variants:createNewVariant")
                : t("studymanager:importcopy")}
            </Button>
          )}
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
