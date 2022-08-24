import { Button, Tooltip } from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useTranslation } from "react-i18next";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";
import { fetchStudies } from "../../../redux/ducks/studies";

interface Props {
  showLabel?: boolean;
}

function RefreshButton(props: Props) {
  const { showLabel } = props;
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  const buttonProps = {
    endIcon: showLabel ? <RefreshIcon /> : undefined,
    children: showLabel ? t("studies.refresh") : <RefreshIcon />,
  };

  return (
    <Tooltip title={t("studies.refresh") as string} sx={{ mr: 4 }}>
      <Button
        color="primary"
        onClick={() => dispatch(fetchStudies())}
        variant="outlined"
        {...buttonProps}
      />
    </Tooltip>
  );
}

export default RefreshButton;
