import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";

interface ViewMatrixButtonProps {
  label: string;
  onClick: () => void;
}

function ViewMatrixButton({ label, onClick }: ViewMatrixButtonProps) {
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
