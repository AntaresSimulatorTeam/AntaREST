import { Box, Tooltip, Typography, Chip, Button } from "@mui/material";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";
import { StudyMetadata, StudyType } from "../../../../common/types";
import { toggleFavorite } from "../../../../redux/ducks/studies";
import StarToggle from "../../../common/StarToggle";
import useAppDispatch from "../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../redux/hooks/useAppSelector";
import { isCurrentStudyFavorite } from "../../../../redux/selectors";

interface Props {
  study: StudyMetadata | undefined;
  isExplorer: boolean | undefined;
  onCopyId: () => Promise<void>;
  onUnarchive: () => Promise<void>;
  onLaunch: VoidFunction;
  onOpenCommands: VoidFunction;
}

function NavHeaderCommands({
  study,
  isExplorer,
  onCopyId,
  onUnarchive,
  onLaunch,
  onOpenCommands,
}: Props) {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const isStudyFavorite = useAppSelector(isCurrentStudyFavorite);
  const isManaged = study?.managed;
  const isArchived = study?.archived;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (!study) {
    return null;
  }

  return (
    <Box
      sx={{
        width: 1,
        display: "flex",
        flexDirection: "row",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Tooltip title={study.folder} placement="bottom-start">
        <Typography
          variant="h6"
          noWrap
          sx={{
            width: 1,
          }}
        >
          {study.name}
        </Typography>
      </Tooltip>
      <StarToggle
        isActive={isStudyFavorite}
        activeTitle={t("studies.removeFavorite")}
        unactiveTitle={t("studies.addFavorite")}
        onToggle={() => dispatch(toggleFavorite(study.id))}
      />
      <Tooltip title={t("study.copyId")}>
        <ContentCopyIcon
          sx={{
            cursor: "pointer",
            width: 16,
            height: 16,
            mx: 1,
            color: "text.secondary",
            "&:hover": { color: "primary.main" },
          }}
          onClick={onCopyId}
        />
      </Tooltip>
      {isManaged ? (
        <Chip
          label={t("study.managedStudy")}
          variant="filled"
          color="info"
          size="small"
          sx={{ mr: 1 }}
        />
      ) : (
        <Chip
          label={study.workspace}
          variant="filled"
          size="small"
          sx={{ mr: 1 }}
        />
      )}
      {(study.tags || []).map((tag) => (
        <Chip
          key={tag}
          label={tag}
          variant="filled"
          size="small"
          sx={{ mr: 1 }}
        />
      ))}
      {isExplorer && (
        <Button
          size="small"
          variant="contained"
          color="primary"
          onClick={isArchived ? onUnarchive : onLaunch}
          sx={{ minWidth: isArchived ? 100 : 0, ml: 1 }}
        >
          {isArchived ? t("global.unarchive") : t("global.launch")}
        </Button>
      )}
      {study.type === StudyType.VARIANT && (
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={onOpenCommands}
          sx={{ minWidth: 0, ml: 2 }}
        >
          <HistoryOutlinedIcon />
        </Button>
      )}
    </Box>
  );
}

export default NavHeaderCommands;
