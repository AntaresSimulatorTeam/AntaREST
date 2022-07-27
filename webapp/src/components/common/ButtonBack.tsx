import { Box, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";

interface Props {
  onClick: VoidFunction;
}

function ButtonBack(props: Props) {
  const { onClick } = props;
  const [t] = useTranslation();

  return (
    <Box
      width="100%"
      display="flex"
      flexDirection="row"
      justifyContent="flex-start"
      alignItems="center"
      boxSizing="border-box"
    >
      <ArrowBackIcon
        color="secondary"
        onClick={() => onClick()}
        sx={{ cursor: "pointer" }}
      />
      <Button variant="text" color="secondary" onClick={() => onClick()}>
        {t("button.back")}
      </Button>
    </Box>
  );
}

export default ButtonBack;
