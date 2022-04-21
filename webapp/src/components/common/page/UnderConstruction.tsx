import ConstructionIcon from "@mui/icons-material/Construction";
import { Box, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

interface Props {
  previewImage?: string;
}

function UnderConstruction(props: Props) {
  const { previewImage } = props;
  const { t } = useTranslation();
  return (
    <Box
      sx={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Box
        sx={{
          height: "75%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <ConstructionIcon sx={{ width: "100px", height: "100px" }} />
        <Typography>{t("main:underConstruction")}</Typography>
      </Box>
      {previewImage ? (
        <Box
          sx={{
            flexGrow: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            width: "100%",
            mb: 6,
          }}
        >
          <Paper sx={{ display: "flex", width: "60%", p: 2 }}>
            <Box width="40%">
              <Typography>PREVIEW</Typography>
            </Box>
            <Box
              sx={{ width: "60%", display: "flex", justifyContent: "center" }}
            >
              <img height="200px" src={previewImage} alt="preview" />
            </Box>
          </Paper>
        </Box>
      ) : undefined}
    </Box>
  );
}

UnderConstruction.defaultProps = {
  previewImage: undefined,
};

export default UnderConstruction;
