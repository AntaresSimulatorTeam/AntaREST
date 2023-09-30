import { Box, Tooltip, Typography, Chip, Button, Divider } from "@mui/material";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useTranslation } from "react-i18next";
import MoreVertIcon from "@mui/icons-material/MoreVert";
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
  onOpenMenu: React.MouseEventHandler;
}

function Actions({
  study,
  isExplorer,
  onCopyId,
  onUnarchive,
  onLaunch,
  onOpenCommands,
  onOpenMenu,
}: Props) {
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const isStudyFavorite = useAppSelector(isCurrentStudyFavorite);
  const isManaged = study?.managed;
  const isArchived = study?.archived;

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
        gap: 2,
      }}
    >
      <Tooltip title={study.folder} placement="bottom-start">
        <Typography
          variant="h6"
          noWrap
          sx={{
            flex: 1,
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
        />
      ) : (
        <Chip label={study.workspace} variant="filled" size="small" />
      )}
      {study.tags?.map((tag) => (
        <Chip key={tag} label={tag} variant="filled" size="small" />
      ))}
      {isExplorer && (
        <Button
          size="small"
          variant="contained"
          color="primary"
          onClick={isArchived ? onUnarchive : onLaunch}
        >
          {isArchived ? t("global.unarchive") : t("global.launch")}
        </Button>
      )}
      <Divider flexItem orientation="vertical" />
      {study.type === StudyType.VARIANT && (
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={onOpenCommands}
          sx={{ minWidth: 0 }}
        >
          <HistoryOutlinedIcon />
        </Button>
      )}
      <Button
        size="small"
        variant="outlined"
        color="primary"
        sx={{ width: "auto", minWidth: 0, px: 0 }}
        onClick={onOpenMenu}
      >
        <MoreVertIcon />
      </Button>
    </Box>
  );
}

export default Actions;
