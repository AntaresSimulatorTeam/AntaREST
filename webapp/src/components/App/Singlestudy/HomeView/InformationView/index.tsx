import { useState } from "react";
import { Paper, Button, Box, Divider } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AxiosError } from "axios";
import { StudyMetadata, VariantTree } from "../../../../../common/types";
import CreateVariantDialog from "./CreateVariantDialog";
import LauncherHistory from "./LauncherHistory";
import Notes from "./Notes";
import LauncherDialog from "../../../Studies/LauncherDialog";
import {
  copyStudy,
  unarchiveStudy as callUnarchiveStudy,
} from "../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";

interface Props {
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
      await copyStudy(
        study.id,
        `${study.name} (${t("studies.copySuffix")})`,
        false,
      );
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.copyStudy"), e as AxiosError);
    }
  };

  const unarchiveStudy = async (study: StudyMetadata) => {
    try {
      await callUnarchiveStudy(study.id);
    } catch (e) {
      enqueueErrorSnackbar(
        t("studies.error.unarchive", { studyname: study.name }),
        e as AxiosError,
      );
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
        {study && <Notes study={study} />}
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
              if (study) {
                navigate(`/studies/${study.id}/explore`);
              }
            }}
          >
            {t("global.open")}
          </Button>
          {study && !study.archived && (
            <Button
              variant="text"
              color="primary"
              onClick={() =>
                study.managed ? setOpenVariantModal(true) : importStudy(study)
              }
              sx={{ mx: 2 }}
            >
              {study.managed
                ? t("variants.createNewVariant")
                : t("studies.importcopy")}
            </Button>
          )}
        </Box>
        <Button
          variant="contained"
          color="primary"
          onClick={
            study?.archived
              ? () => {
                  unarchiveStudy(study);
                }
              : () => setOpenLauncherModal(true)
          }
        >
          {study?.archived ? t("global.unarchive") : t("global.launch")}
        </Button>
      </Box>
      {study && tree && openVariantModal && (
        <CreateVariantDialog
          parentId={study.id}
          open={openVariantModal}
          onClose={() => setOpenVariantModal(false)}
          tree={tree}
        />
      )}
      {study && openLauncherModal && (
        <LauncherDialog
          open={openLauncherModal}
          studyIds={[study.id]}
          onClose={() => setOpenLauncherModal(false)}
        />
      )}
    </Paper>
  );
}

export default InformationView;
