import { Box, Button, Divider, Tooltip } from "@mui/material";
import SplitButton from "../buttons/SplitButton";
import DownloadMatrixButton from "../DownloadMatrixButton";
import FileDownload from "@mui/icons-material/FileDownload";
import { useTranslation } from "react-i18next";
import { LoadingButton } from "@mui/lab";
import Save from "@mui/icons-material/Save";
import { Undo, Redo } from "@mui/icons-material";

interface MatrixActionsProps {
  onImport: VoidFunction;
  onSave: VoidFunction;
  studyId: string;
  path: string;
  disabled: boolean;
  pendingUpdatesCount: number;
  isSubmitting: boolean;
  undo: VoidFunction;
  redo: VoidFunction;
  canUndo: boolean;
  canRedo: boolean;
}

function MatrixActions({
  onImport,
  onSave,
  studyId,
  path,
  disabled,
  pendingUpdatesCount,
  isSubmitting,
  undo,
  redo,
  canUndo,
  canRedo,
}: MatrixActionsProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Tooltip title={t("global.undo")}>
        <span>
          <Button onClick={undo} disabled={!canUndo} startIcon={<Undo />} />
        </span>
      </Tooltip>
      <Tooltip title={t("global.redo")}>
        <span>
          <Button onClick={redo} disabled={!canRedo} startIcon={<Redo />} />
        </span>
      </Tooltip>
      <LoadingButton
        onClick={onSave}
        loading={isSubmitting}
        loadingPosition="start"
        startIcon={<Save />}
        variant="contained"
        size="small"
        disabled={pendingUpdatesCount === 0}
      >
        ({pendingUpdatesCount})
      </LoadingButton>
      <Divider sx={{ mx: 2 }} orientation="vertical" flexItem />
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
