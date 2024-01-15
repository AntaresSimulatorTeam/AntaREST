import { useState } from "react";
import { AxiosError } from "axios";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { Button } from "@mui/material";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { getStudyData, importFile } from "../../../../../../services/api/study";
import { Content, Header, Root } from "./style";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import ImportDialog from "../../../../../common/dialogs/ImportDialog";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import { useDebugContext } from "../DebugContext";

interface Props {
  studyId: string;
  path: string;
}

function Text({ studyId, path }: Props) {
  const [t] = useTranslation();
  const { reloadTreeData } = useDebugContext();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openImportDialog, setOpenImportDialog] = useState(false);

  const res = usePromiseWithSnackbarError(() => getStudyData(studyId, path), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [studyId, path],
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport = async (file: File) => {
    try {
      await importFile(file, studyId, path);
      reloadTreeData();
      enqueueSnackbar(t("studies.success.saveData"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Header>
        <Button
          variant="outlined"
          color="primary"
          startIcon={<UploadOutlinedIcon />}
          onClick={() => setOpenImportDialog(true)}
          sx={{ mb: 1 }}
        >
          {t("global.import")}
        </Button>
      </Header>
      <UsePromiseCond
        response={res}
        ifResolved={(data) => (
          <Content>
            <code style={{ whiteSpace: "pre" }}>{data}</code>
          </Content>
        )}
      />
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          onClose={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
    </Root>
  );
}

export default Text;
