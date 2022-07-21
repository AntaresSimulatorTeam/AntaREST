import { styled, experimental_sx as sx } from "@mui/material";
import Fieldset from "../../../../../../../common/Fieldset";

export const StyledFieldset = styled(Fieldset)(
  sx({
    p: 0,
    pb: 5,
    ".MuiBox-root": {
      display: "flex",
      flexWrap: "wrap",
      gap: 2,
      ".MuiFormControl-root": {
        width: 220,
      },
    },
  })
);
