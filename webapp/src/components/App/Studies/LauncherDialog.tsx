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
  Stack,
  Switch,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useMountedState } from "react-use";
import { shallowEqual } from "react-redux";
import {
  StudyMetadata,
  StudyOutput,
  LaunchOptions,
} from "../../../common/types";
import {
  getLauncherLoad,
  getLauncherVersions,
  getStudyOutputs,
  launchStudy,
} from "../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../redux/selectors";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import LinearProgressWithLabel from "../../common/LinearProgressWithLabel";
import SelectSingle from "../../common/SelectSingle";
import CheckBoxFE from "../../common/fieldEditors/CheckBoxFE";
import { convertVersions } from "../../../services/utils";

const LAUNCH_DURATION_MAX_HOURS = 240;
const LAUNCH_LOAD_DEFAULT = 22;
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
    auto_unzip: true,
  });
  const [solverVersion, setSolverVersion] = useState<string>();
  const [isLaunching, setIsLaunching] = useState(false);
  const isMounted = useMountedState();
  const studyNames = useAppSelector(
    (state) => studyIds.map((sid) => getStudy(state, sid)?.name),
    shallowEqual,
  );

  const { data: load } = usePromiseWithSnackbarError(() => getLauncherLoad(), {
    errorMessage: t("study.error.launchLoad"),
    deps: [open],
  });

  const { data: outputList } = usePromiseWithSnackbarError(
    () => Promise.all(studyIds.map((sid) => getStudyOutputs(sid))),
    { errorMessage: t("study.error.listOutputs"), deps: [studyIds] },
  );

  const { data: launcherVersions = [] } = usePromiseWithSnackbarError(
    async () => convertVersions(await getLauncherVersions()),
    { errorMessage: t("study.error.launcherVersions") },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleLaunchClick = async () => {
    if (studyIds.length > 0) {
      setIsLaunching(true);
      Promise.all(
        studyIds.map((sid) => launchStudy(sid, options, solverVersion)),
      )
        .then(() => {
          enqueueSnackbar(
            t("studies.studylaunched", {
              studyname: studyNames.join(", "),
            }),
            {
              variant: "success",
            },
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
    value: LaunchOptions[T],
  ) => {
    setOptions((prevOptions) => ({
      ...prevOptions,
      [field]: value,
    }));
  };

  const handleObjectChange = <T extends keyof LaunchOptions>(
    field: T,
    value: object,
  ) => {
    setOptions((prevOptions: LaunchOptions) => {
      return {
        ...prevOptions,
        [field]: { ...(prevOptions[field] as object), ...value },
      };
    });
  };

  const handleOtherOptionsChange = (
    optionChanges: Array<{ option: string; active: boolean }>,
  ) => {
    setOptions((prevOptions) => {
      const { other_options: prevOtherOptions = "" } = prevOptions;
      const { toAdd, toRemove } = optionChanges.reduce(
        (acc, item) => {
          acc[item.active ? "toAdd" : "toRemove"].push(item.option);
          return acc;
        },
        { toAdd: [], toRemove: [] } as { toAdd: string[]; toRemove: string[] },
      );
      return {
        ...prevOptions,
        other_options: R.without(toRemove, prevOtherOptions.split(/\s+/))
          .concat(toAdd)
          .join(" "),
      };
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
              <LinearProgressWithLabel
                indicator={load.slurm * 100}
                size="30%"
                tooltip={t("study.clusterLoad")}
                gradiant
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
        <Typography sx={{ mt: 1 }}>Xpansion</Typography>
        <FormGroup
          sx={{
            mt: 1,
            mx: 1,
            width: "100%",
          }}
        >
          <Box sx={{ display: "flex" }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={!!options.xpansion}
                  onChange={(e, checked) => {
                    handleChange(
                      "xpansion",
                      checked ? { enabled: true } : undefined,
                    );
                  }}
                />
              }
              label={t("study.xpansionMode") as string}
            />
          </Box>
          {outputList && outputList.length === 1 && (
            <Box sx={{ display: "flex" }}>
              <FormControlLabel
                control={
                  <Checkbox
                    disabled={!!options.xpansion_r_version || !options.xpansion}
                    checked={options.xpansion?.sensitivity_mode || false}
                    onChange={(e, checked) =>
                      handleObjectChange("xpansion", {
                        sensitivity_mode: checked,
                      })
                    }
                  />
                }
                label={t("launcher.xpansion.sensitivityMode") as string}
              />
              <SelectSingle
                name={t("studies.selectOutput")}
                list={outputList[0].map((o: StudyOutput) => ({
                  id: o.name,
                  name: o.name,
                }))}
                disabled={!!options.xpansion_r_version || !options.xpansion}
                data={options.xpansion?.output_id || ""}
                setValue={(data: string) =>
                  handleObjectChange("xpansion", {
                    output_id: data,
                  })
                }
                sx={{ width: "300px", my: 3 }}
              />
            </Box>
          )}
          <Box>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography>{t("launcher.xpansion.versionR")}</Typography>
              <Switch
                checked={!options.xpansion_r_version}
                disabled={!options.xpansion}
                onChange={(e, checked) =>
                  handleChange("xpansion_r_version", !checked)
                }
              />
              <Typography>{t("launcher.xpansion.versionCpp")}</Typography>
            </Stack>
          </Box>
        </FormGroup>
        <Typography sx={{ mt: 1 }}>Adequacy Patch</Typography>
        <FormGroup
          sx={{
            mt: 1,
            mx: 1,
            width: "100%",
          }}
        >
          <Box>
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
            <FormControlLabel
              control={
                <Checkbox
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  checked={!!(options.adequacy_patch as any)?.legacy}
                  onChange={(e, checked) =>
                    handleChange(
                      "adequacy_patch",
                      checked ? { legacy: true } : {},
                    )
                  }
                />
              }
              label="Adequacy patch non linearized"
            />
          </Box>
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
              <FormControlLabel
                control={
                  <Checkbox
                    checked={!!options.auto_unzip}
                    onChange={(e, checked) =>
                      handleChange("auto_unzip", checked)
                    }
                  />
                }
                label={t("launcher.autoUnzip")}
              />
            </FormControl>
            <FormControl
              sx={{
                mt: 2,
                width: "100%",
              }}
            >
              <CheckBoxFE
                label={t("launcher.xpress")}
                value={!!options.other_options?.match("xpress")}
                onChange={(e, checked) =>
                  handleOtherOptionsChange([
                    { option: "xpress", active: checked },
                  ])
                }
              />
            </FormControl>
            <SelectSingle
              name={t("global.version")}
              list={launcherVersions}
              data={solverVersion}
              setValue={setSolverVersion}
              sx={{ width: 1, mt: 2 }}
            />
            <FormControl
              sx={{
                mt: 2,
                width: 1,
              }}
            >
              <TextField
                label={t("study.otherOptions")}
                type="text"
                variant="filled"
                value={options.other_options}
                onChange={(e) => handleChange("other_options", e.target.value)}
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
