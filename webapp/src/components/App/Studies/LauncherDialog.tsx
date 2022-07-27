import { useState } from "react";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Checkbox,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  List,
  ListItem,
  Slider,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useMountedState } from "react-use";
import { shallowEqual } from "react-redux";
import { StudyMetadata } from "../../../common/types";
import {
  getLauncherLoad,
  LaunchOptions,
  launchStudy,
} from "../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../redux/selectors";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import LoadIndicator from "../../common/LoadIndicator";

const LAUNCH_DURATION_MAX_HOURS = 240;
const LAUNCH_LOAD_DEFAULT = 12;
const LAUNCH_LOAD_SLIDER = { step: 1, min: 1, max: 24 };

interface Props {
  open: boolean;
  studyIds: Array<StudyMetadata["id"]>;
  onClose: () => void;
}

function LauncherDialog(props: Props) {
  const { studyIds, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const theme = useTheme();
  const [options, setOptions] = useState<LaunchOptions>({
    nb_cpu: LAUNCH_LOAD_DEFAULT,
  });
  const [solverVersion, setSolverVersion] = useState<string>();
  const [isLaunching, setIsLaunching] = useState(false);
  const isMounted = useMountedState();
  const studyNames = useAppSelector(
    (state) => studyIds.map((sid) => getStudy(state, sid)?.name),
    shallowEqual
  );

  const { data: load } = usePromiseWithSnackbarError(() => getLauncherLoad(), {
    errorMessage: t("study.error.launchLoad"),
    deps: [open],
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLaunchClick = async () => {
    if (studyIds.length > 0) {
      setIsLaunching(true);
      Promise.all(
        studyIds.map((sid) => launchStudy(sid, options, solverVersion))
      )
        .then(() => {
          enqueueSnackbar(
            t("studies.studylaunched", {
              studyname: studyNames.join(", "),
            }),
            {
              variant: "success",
            }
          );
          onClose();
        })
        .catch((err) => {
          enqueueErrorSnackbar(t("studies.error.runStudy"), err);
        })
        .finally(() => {
          if (isMounted()) {
            setIsLaunching(false);
          }
        });
    }
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
            disabled={isLaunching}
            onClick={handleLaunchClick}
          >
            {t("global.launch")}
          </Button>
        </>
      }
    >
      <Box
        sx={{
          minWidth: "100px",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "flex-start",
          alignItems: "flex-start",
          px: 2,
          boxSizing: "border-box",
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        <Divider
          sx={{ width: "100%", height: "1px" }}
          orientation="horizontal"
        />
        <Box
          sx={{
            mb: 1,
            width: "100%",
          }}
        >
          <Box
            sx={{
              width: "100%",
              maxHeight: "200px",
              overflow: "auto",
            }}
          >
            {studyNames.length === 1 ? (
              <Typography variant="caption">{studyNames[0]}</Typography>
            ) : (
              <List>
                {studyNames.map((name) => (
                  <ListItem key={name}>
                    <Typography variant="caption">{name}</Typography>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Box>
        <Divider
          sx={{ width: "100%", height: "1px", mb: 1 }}
          orientation="horizontal"
        />
        <Typography
          sx={{
            fontSize: "1.1rem",
            fontWeight: "bold",
            mb: 2,
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
            variant="filled"
            value={options.output_suffix}
            onChange={(e) =>
              handleChange("output_suffix", e.target.value.trim())
            }
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
            mt: 2,
            width: "100%",
          }}
        >
          <TextField
            id="launcher-option-time-limit"
            label={t("study.timeLimit")}
            type="number"
            variant="filled"
            value={
              (options.time_limit === undefined ? 172800 : options.time_limit) /
              3600
            }
            onChange={(e) =>
              handleChange("time_limit", timeLimitParse(e.target.value))
            }
            InputLabelProps={{
              shrink: true,
              sx: {
                ".MuiInputLabel-root": {
                  color: theme.palette.text.secondary,
                },
                ".Mui-focused": {},
              },
            }}
            helperText={t("study.timeLimitHelper", {
              max: LAUNCH_DURATION_MAX_HOURS,
            })}
          />
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              width: "100%",
            }}
          >
            <Typography sx={{ mt: 1 }}>{t("study.nbCpu")}</Typography>
            {load && (
              <LoadIndicator
                indicator={load.slurm}
                size="30%"
                tooltip={t("study.clusterLoad")}
              />
            )}
          </Box>
          <Slider
            sx={{
              width: "95%",
              mx: 1,
            }}
            defaultValue={LAUNCH_LOAD_DEFAULT}
            step={LAUNCH_LOAD_SLIDER.step}
            min={LAUNCH_LOAD_SLIDER.min}
            color="secondary"
            max={LAUNCH_LOAD_SLIDER.max}
            valueLabelDisplay="auto"
            onChange={(event, val) => handleChange("nb_cpu", val as number)}
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
                variant="filled"
                value={options.other_options}
                onChange={(e) =>
                  handleChange("other_options", e.target.value.trim())
                }
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
                mt: 2,
              }}
            >
              <TextField
                id="launcher-version"
                label={t("global.version")}
                type="text"
                variant="filled"
                value={solverVersion}
                onChange={(e) => setSolverVersion(e.target.value.trim())}
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
      </Box>
    </BasicDialog>
  );
}

export default LauncherDialog;
