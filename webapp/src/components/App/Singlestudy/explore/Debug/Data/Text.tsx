import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@mui/material";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { getStudyData, importFile } from "../../../../../../services/api/study";
import { Content, Header, Root } from "./style";
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
  const [openImportDialog, setOpenImportDialog] = useState(false);

  const res = usePromiseWithSnackbarError(() => getStudyData(studyId, path), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [studyId, path],
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport = async (file: File) => {
    await importFile(file, studyId, path);
    reloadTreeData();
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
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
    </Root>
  );
}

export default Text;
