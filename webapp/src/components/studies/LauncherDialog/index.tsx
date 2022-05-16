import { useState } from "react";
import {
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { StudyMetadata } from "../../../common/types";
import { LaunchOptions, launchStudy } from "../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import { Root } from "./style";

interface Props {
  open: boolean;
  study?: StudyMetadata;
  onClose: () => void;
}

function LauncherModal(props: Props) {
  const { study, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const theme = useTheme();
  const [options, setOptions] = useState<LaunchOptions>({});

  const launch = async () => {
    if (!study) {
      enqueueSnackbar(t("studymanager:failtorunstudy"), { variant: "error" });
      return;
    }
    try {
      await launchStudy(study.id, options);
      enqueueSnackbar(
        t("studymanager:studylaunched", { studyname: study.name }),
        { variant: "success" }
      );
      onClose();
    } catch (e) {
      enqueueErrorSnackbar(t("studymanager:failtorunstudy"), e as AxiosError);
    }
  };

  const handleChange = (
    field: string,
    value: number | string | boolean | object | undefined
  ) => {
    setOptions({
      ...options,
      [field]: value,
    });
  };

  const timeLimitParse = (value: string): number => {
    try {
      return parseInt(value, 10) * 3600;
    } catch {
      return 48 * 3600;
    }
  };

  return (
    <BasicDialog
      title={t("singlestudy:runStudy")}
      open={open}
      onClose={onClose}
      contentProps={{
        sx: { width: "500px", height: "450px", p: 0, overflow: "hidden" },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global:global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={launch}
          >
            {t("main:launch")}
          </Button>
        </>
      }
    >
      <Root>
        <Typography
          sx={{
            fontSize: "1.2em",
            fontWeight: "bold",
            mb: 3,
          }}
        >
          Options
        </Typography>
        <FormControl
          sx={{
            width: "100%",
          }}
        >
          <TextField
            id="launcher-option-output-suffix"
            label={t("main:name")}
            type="text"
            value={options.output_suffix}
            onChange={(e) =>
              handleChange("output_suffix", e.target.value.trim())
            }
            InputProps={{
              sx: {
                ".MuiOutlinedInput-root": {
                  "&.MuiOutlinedInput-notchedOutline": {
                    borderColor: `${theme.palette.primary.main} !important`,
                  },
                },
                ".Mui-focused": {
                  // borderColor: `${theme.palette.primary.main} !important`
                },
                ".MuiOutlinedInput-notchedOutline": {
                  borderWidth: "1px",
                  borderColor: `${theme.palette.text.secondary} !important`,
                },
              },
            }}
            InputLabelProps={{
              shrink: true,
              sx: {
                ".MuiInputLabel-root": {
                  color: theme.palette.text.secondary,
                },
                ".Mui-focused": {},
              },
            }}
          />
        </FormControl>
        <FormControl
          sx={{
            mt: 1,
            width: "100%",
          }}
        >
          <TextField
            id="launcher-option-time-limit"
            label={t("singlestudy:timeLimit")}
            type="number"
            value={
              (options.time_limit === undefined ? 172800 : options.time_limit) /
              3600
            }
            onChange={(e) =>
              handleChange("time_limit", timeLimitParse(e.target.value))
            }
            InputProps={{
              sx: {
                ".MuiOutlinedInput-root": {
                  "&.MuiOutlinedInput-notchedOutline": {
                    borderColor: `${theme.palette.primary.main} !important`,
                  },
                },
                ".Mui-focused": {
                  // borderColor: `${theme.palette.primary.main} !important`
                },
                ".MuiOutlinedInput-notchedOutline": {
                  borderWidth: "1px",
                  borderColor: `${theme.palette.text.secondary} !important`,
                },
              },
            }}
            InputLabelProps={{
              shrink: true,
              sx: {
                ".MuiInputLabel-root": {
                  color: theme.palette.text.secondary,
                },
                ".Mui-focused": {},
              },
            }}
            helperText={t("singlestudy:timeLimitHelper")}
          />
        </FormControl>
        <FormGroup
          sx={{
            mt: 1,
            width: "100%",
          }}
        >
          <FormControlLabel
            control={
              <Checkbox
                checked={!!options.xpansion}
                onChange={(e, checked) => {
                  handleChange("xpansion", checked);
                }}
              />
            }
            label={t("singlestudy:xpansionMode") as string}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={!!options.xpansion && !!options.xpansion_r_version}
                onChange={(e, checked) =>
                  handleChange("xpansion_r_version", checked)
                }
              />
            }
            label={t("singlestudy:useXpansionVersionR") as string}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={!!options.adequacy_patch}
                onChange={(e, checked) =>
                  handleChange("adequacy_patch", checked ? {} : undefined)
                }
              />
            }
            label="Adequacy patch"
          />
        </FormGroup>
      </Root>
    </BasicDialog>
  );
}

LauncherModal.defaultProps = {
  study: undefined,
};

export default LauncherModal;
