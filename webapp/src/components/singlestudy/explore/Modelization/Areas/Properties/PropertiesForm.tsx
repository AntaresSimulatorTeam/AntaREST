import { Box, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import Fieldset from "../../../../../common/Fieldset";
import { FormObj } from "../../../../../common/Form";
import { PropertiesFields } from "./utils";

export default function PropertiesForm(
  formObj: FormObj<PropertiesFields, any>
) {
  const {
    control,
    register,
    getValues,
    formState: { errors },
    defaultValues,
  } = formObj;
  const [t] = useTranslation();
  console.log(formObj);
  return (
    <Fieldset title={t("global.general")} style={{ padding: "16px" }}>
      <Box
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <TextField
          sx={{ mx: 1 }}
          label={t("study.modelization.map.areaName")}
          variant="filled"
          value="jj"
          disabled
        />
        <TextField
          sx={{ mx: 1 }}
          label={t("study.modelization.posX")}
          variant="filled"
          value="23"
        />
        <TextField
          sx={{ mx: 1 }}
          label={t("study.modelization.posY")}
          variant="filled"
          value="456"
        />
      </Box>
    </Fieldset>
  );
}
