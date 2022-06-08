import { useState } from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { StudyMetadata } from "../../../common/types";
import { LaunchOptions, launchStudy } from "../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import { Root } from "./style";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../redux/selectors";

interface Props {
  open: boolean;
  studyId: StudyMetadata["id"];
  onClose: () => void;
}

function LauncherModal(props: Props) {
  const { studyId, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const theme = useTheme();
  const [options, setOptions] = useState<LaunchOptions>({});
  const [solverVersion, setSolverVersion] = useState<string>();
  const studyName = useAppSelector((state) => getStudy(state, studyId)?.name);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLaunchClick = async () => {
    launchStudy(studyId, options, solverVersion)
      .then(() => {
        enqueueSnackbar(t("studies.studylaunched", { studyname: studyName }), {
          variant: "success",
        });
        onClose();
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.runStudy"), err);
      });
  };

  const handleChange = <T extends keyof LaunchOptions>(
    field: T,
    value: LaunchOptions[T]
  ) => {
    setOptions({
      ...options,
      [field]: value,
    });
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const timeLimitParse = (value: string): number => {
    try {
      return parseInt(value, 10) * 3600;
    } catch {
      return 48 * 3600;
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.runStudy")}
      open={open}
      onClose={onClose}
      contentProps={{
        sx: { width: "500px", height: "500px", p: 0, overflow: "hidden" },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={handleLaunchClick}
          >
            {t("global.launch")}
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
            label={t("global.name")}
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
            label={t("study.timeLimit")}
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
            helperText={t("study.timeLimitHelper")}
          />
        </FormControl>
        <FormGroup
          sx={{
            mt: 1,
            mx: 1,
            width: "100%",
          }}
        >
          <FormControlLabel
            control={
              <Checkbox
                checked={!!options.archive_output}
                onChange={(e, checked) => {
                  handleChange("archive_output", checked);
                }}
              />
            }
            label={t("study.archiveOutputMode") as string}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={!!options.xpansion}
                onChange={(e, checked) => {
                  handleChange("xpansion", checked);
                }}
              />
            }
            label={t("study.xpansionMode") as string}
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
            label={t("study.useXpansionVersionR") as string}
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
        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="panel-advanced-parameters"
            id="panel-advanced-parameters-header"
          >
            <Typography>{t("global.advancedParams")}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <FormControl
              sx={{
                width: "100%",
              }}
            >
              <TextField
                id="launcher-option-other-options"
                label={t("study.otherOptions")}
                type="text"
                value={options.other_options}
                onChange={(e) =>
                  handleChange("other_options", e.target.value.trim())
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
                width: "100%",
              }}
            >
              <TextField
                id="launcher-version"
                label={t("global.version")}
                type="text"
                value={solverVersion}
                onChange={(e) => setSolverVersion(e.target.value.trim())}
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
          </AccordionDetails>
        </Accordion>
      </Root>
    </BasicDialog>
  );
}

export default LauncherModal;
