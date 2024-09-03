import { Box } from "@mui/material";
import SplitButton from "../buttons/SplitButton";
import DownloadMatrixButton from "../DownloadMatrixButton";
import FileDownload from "@mui/icons-material/FileDownload";
import { useTranslation } from "react-i18next";

interface MatrixActionsProps {
  onImport: () => void;
  studyId: string;
  path: string;
  disabled: boolean;
}

function MatrixActions({
  onImport,
  studyId,
  path,
  disabled,
}: MatrixActionsProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <SplitButton
        options={[t("global.import.fromFile"), t("global.import.fromDatabase")]}
        onClick={onImport}
        size="small"
        ButtonProps={{
          startIcon: <FileDownload />,
        }}
      >
        {t("global.import")}
      </SplitButton>
      <DownloadMatrixButton studyId={studyId} path={path} disabled={disabled} />
    </Box>
  );
}

export default MatrixActions;
