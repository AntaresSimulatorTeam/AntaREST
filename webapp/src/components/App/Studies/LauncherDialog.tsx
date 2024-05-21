import { useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  FormGroup,
  List,
  ListItem,
  Skeleton,
  TextField,
  Typography,
} from "@mui/material";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useMountedState } from "react-use";
import { shallowEqual } from "react-redux";
import {
  LaunchOptions,
  StudyMetadata,
  StudyOutput,
} from "../../../common/types";
import {
  getLauncherCores,
  getLauncherTimeLimit,
  getLauncherVersions,
  getStudyOutputs,
  launchStudy,
} from "../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import BasicDialog from "../../common/dialogs/BasicDialog";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../redux/selectors";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import SelectSingle from "../../common/SelectSingle";
import CheckBoxFE from "../../common/fieldEditors/CheckBoxFE";
import { convertVersions } from "../../../services/utils";
import UsePromiseCond from "../../common/utils/UsePromiseCond";
import SwitchFE from "../../common/fieldEditors/SwitchFE";
import moment from "moment";

const DEFAULT_NB_CPU = 22;
const MIN_TIME_LIMIT = 1 * 3600; // 1 hour in seconds.
const MAX_TIME_LIMIT = 240 * 3600; // 240 hours in seconds.

interface Props {
  open: boolean;
  studyIds: Array<StudyMetadata["id"]>;
  onClose: () => void;
}

function LauncherDialog(props: Readonly<Props>) {
  const { studyIds, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [options, setOptions] = useState<LaunchOptions>({
    nb_cpu: DEFAULT_NB_CPU,
    auto_unzip: true,
    time_limit: MIN_TIME_LIMIT,
  });
  const [solverVersion, setSolverVersion] = useState<string>();
  const [isLaunching, setIsLaunching] = useState(false);
  const isMounted = useMountedState();
  const studyNames = useAppSelector(
    (state) => studyIds.map((sid) => getStudy(state, sid)?.name),
    shallowEqual,
  );

  const launcherCores = usePromiseWithSnackbarError(
    () =>
      getLauncherCores().then((cores) => {
        setOptions((prevOptions) => {
          return {
            ...prevOptions,
            nb_cpu: cores.defaultValue,
          };
        });
        return cores;
      }),
    {
      errorMessage: t("study.error.launcherCores"),
    },
  );

  const launcherTimeLimit = usePromiseWithSnackbarError(
    () =>
      getLauncherTimeLimit().then((timeLimit) => {
        setOptions((prevOptions) => {
          return {
            ...prevOptions,
            time_limit: timeLimit,
          };
        });
        return timeLimit;
      }),
    {
      errorMessage: t("study.error.launcherTimeLimit"),
    },
  );

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

  const handleLaunchClick = () => {
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
          .join(" ")
          .trim(),
      };
    });
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  /**
   * Parses an hour value from a string and converts it to seconds.
   * If the input is invalid, returns a default value.
   *
   * @param hourString - A string representing the number of hours.
   * @returns The equivalent number of seconds, or a default value for invalid inputs.
   */
  const parseHoursToSeconds = (hourString: string): number => {
    const seconds = moment.duration(hourString, "hours").asSeconds();
    return Math.max(MIN_TIME_LIMIT, Math.min(seconds, MAX_TIME_LIMIT));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.runStudy")}
      open={open}
      onClose={onClose}
      maxWidth="md"
      PaperProps={{ sx: { width: 700 } }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            disabled={isLaunching || !launcherCores.isResolved}
            onClick={handleLaunchClick}
          >
            {t("global.launch")}
          </Button>
        </>
      }
    >
      <Box
        sx={{
          width: 1,
          height: 1,
          display: "flex",
          flexDirection: "column",
          px: 2,
          boxSizing: "border-box",
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        <Box
          sx={{
            mb: 1,
            width: 1,
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
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            gap: 2,
          }}
        >
          <TextField
            id="launcher-option-output-suffix"
            label={t("global.name")}
            type="text"
            variant="outlined"
            value={options.output_suffix}
            onChange={(e) =>
              handleChange("output_suffix", e.target.value.trim())
            }
            InputLabelProps={{
              shrink: true,
            }}
            sx={{
              width: "50%",
            }}
          />

          <UsePromiseCond
            response={launcherTimeLimit}
            ifResolved={(timeLimit) => (
              <TextField
                id="launcher-option-time-limit"
                label={t("study.timeLimit")}
                type="number"
                variant="outlined"
                required
                value={(options.time_limit ?? timeLimit) / 3600} // Convert seconds to hours for display.
                onChange={(e) => {
                  handleChange(
                    "time_limit",
                    parseHoursToSeconds(e.target.value),
                  );
                }}
                InputLabelProps={{
                  shrink: true,
                }}
                inputProps={{
                  min: MIN_TIME_LIMIT,
                  max: MAX_TIME_LIMIT,
                  step: 1,
                }}
                sx={{
                  minWidth: "125px",
                }}
              />
            )}
            ifPending={() => <Skeleton width={125} height={60} />}
            ifRejected={() => <Skeleton width={125} height={60} />}
          />

          <UsePromiseCond
            response={launcherCores}
            ifResolved={(cores) => (
              <TextField
                id="nb-cpu"
                label={t("study.nbCpu")}
                type="number"
                variant="outlined"
                value={options.nb_cpu}
                onChange={(e) => {
                  const newValue = parseInt(e.target.value, 10);
                  handleChange(
                    "nb_cpu",
                    Math.min(Math.max(newValue, cores.min), cores.max),
                  );
                }}
                inputProps={{
                  min: cores.min,
                  max: cores.max,
                }}
                sx={{
                  minWidth: "125px",
                }}
              />
            )}
            ifPending={() => <Skeleton width={125} height={60} />}
            ifRejected={() => <Skeleton width={125} height={60} />}
          />
        </Box>
        <Divider
          sx={{ width: 1, mt: 2, border: "0.5px solid", opacity: 0.7 }}
          orientation="horizontal"
        />
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            width: 1,
          }}
        >
          <Typography>Simulateur</Typography>
          <SelectSingle
            name={t("global.version")}
            variant="outlined"
            list={launcherVersions}
            data={solverVersion}
            setValue={setSolverVersion}
            sx={{ width: 1, mt: 0.5 }}
          />
          <TextField
            id="other-options"
            label={t("study.otherOptions")}
            type="text"
            variant="outlined"
            value={options.other_options}
            onChange={(e) => handleChange("other_options", e.target.value)}
            sx={{
              mt: 2,
              width: 1,
            }}
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            width: 1,
            mt: 1,
          }}
        >
          <CheckBoxFE
            label={t("launcher.xpress")}
            value={!!options.other_options?.match("xpress")}
            onChange={(e, checked) =>
              handleOtherOptionsChange([{ option: "xpress", active: checked }])
            }
          />
          <CheckBoxFE
            label={t("launcher.autoUnzip")}
            value={!!options.auto_unzip}
            onChange={(e, checked) => handleChange("auto_unzip", checked)}
          />
        </Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            width: 1,
            mt: 1,
          }}
        >
          <CheckBoxFE
            label="Adequacy patch R"
            value={!!options.adequacy_patch}
            onChange={(e, checked) => {
              handleChange(
                "adequacy_patch",
                checked ? { legacy: true } : undefined,
              );
              handleOtherOptionsChange([
                { option: "adq_patch_rc", active: checked },
              ]);
            }}
          />
          <CheckBoxFE
            label="Adequacy patch non linearized"
            value={!!options.adequacy_patch?.legacy}
            onChange={(e, checked) =>
              handleChange("adequacy_patch", checked ? { legacy: true } : {})
            }
          />
        </Box>
        <Divider
          sx={{ width: 1, my: 1, border: "0.5px solid", opacity: 0.7 }}
          orientation="horizontal"
        />
        <FormGroup
          sx={{
            mt: 1,
            mx: 1,
            width: "100%",
          }}
        >
          <Box
            sx={{
              display: "flex",
              gap: 1,
              alignItems: "center",
              alignContent: "center",
            }}
          >
            <Typography>Xpansion</Typography>
            <SwitchFE
              value={!!options.xpansion}
              onChange={(e, checked) => {
                handleChange(
                  "xpansion",
                  checked ? { enabled: true } : undefined,
                );
              }}
            />
          </Box>
          {outputList && outputList.length === 1 && (
            <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
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
                label={t("launcher.xpansion.sensitivityMode")}
              />
              <SelectSingle
                name={t("studies.selectOutput")}
                variant="outlined"
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
                sx={{ minWidth: 400 }}
              />
            </Box>
          )}
        </FormGroup>
      </Box>
    </BasicDialog>
  );
}

export default LauncherDialog;
