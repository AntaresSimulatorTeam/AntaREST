import { useRef } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { Box, ButtonBase } from "@mui/material";
import CloudUploadOutlinedIcon from "@mui/icons-material/CloudUploadOutlined";

interface PropTypes {
  onImport: (json: object) => void;
}

function CommandImportButton(props: PropTypes) {
  const { onImport } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const inputRef = useRef<HTMLInputElement | null>(null);

  const onButtonClick = () => {
    if (inputRef.current) {
      inputRef.current.click();
    }
  };

  const onInputClick = (e: React.MouseEvent<HTMLInputElement | MouseEvent>) => {
    if (e && e.target) {
      const element = e.target as HTMLInputElement;
      element.value = "";
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    const reader = new FileReader();
    reader.onload = async (ev: ProgressEvent<FileReader>) => {
      try {
        if (ev.target) {
          const text = ev.target.result;
          const json = JSON.parse(text as string);
          onImport(json);
        }
      } catch (error) {
        enqueueSnackbar(t("variants.error.jsonParsing"), {
          variant: "error",
        });
      }
    };
    if (e.target && e.target.files) {
      reader.readAsText(e.target.files[0]);
    }
  };

  return (
    <Box display="flex" alignItems="center">
      <ButtonBase
        type="submit"
        sx={{ width: "auto", height: "auto" }}
        onClick={onButtonClick}
      >
        <CloudUploadOutlinedIcon
          sx={{
            width: "24px",
            height: "auto",
            cursor: "pointer",
            color: "primary.main",
            mx: 0.5,
            "&:hover": {
              color: "primary.dark",
            },
          }}
        />
      </ButtonBase>
      <input
        style={{ display: "none" }}
        type="file"
        name="file"
        accept="application/json"
        onChange={(e) => handleChange(e)}
        onClick={(e) => onInputClick(e)}
        ref={(e) => {
          inputRef.current = e;
        }}
      />
    </Box>
  );
}

export default CommandImportButton;
