import {
  Toolbar,
  alpha,
  Typography,
  Tooltip,
  IconButton,
  Fade,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";

interface Props {
  numSelected: number;
  handleDelete: () => void;
}

function TableToolbar({ numSelected, handleDelete }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Fade in={numSelected > 0} timeout={300}>
      <Toolbar
        sx={{
          ...(numSelected > 0 && {
            bgcolor: (theme) =>
              alpha(
                theme.palette.primary.main,
                theme.palette.action.activatedOpacity,
              ),
          }),
        }}
      >
        {numSelected > 0 && (
          <>
            <Typography sx={{ flex: 1 }}>
              {numSelected} {t("global.selected")}
            </Typography>
            <Tooltip title={t("global.delete")}>
              <IconButton onClick={handleDelete}>
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </>
        )}
      </Toolbar>
    </Fade>
  );
}

export default TableToolbar;
