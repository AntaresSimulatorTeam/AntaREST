import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  label: string;
  onClick: () => void;
}

function ViewMatrixButton({ label, onClick }: Props) {
  const { t } = useTranslation();

  return (
    <Button
      variant="outlined"
      size="small"
      sx={{ mt: 3, mr: 3 }}
      onClick={onClick}
    >
      {t(label)}
    </Button>
  );
}

export default ViewMatrixButton;
