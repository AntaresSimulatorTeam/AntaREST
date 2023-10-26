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
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useMountedState } from "react-use";
import { shallowEqual } from "react-redux";
import {
  StudyMetadata,
  StudyOutput,
  LaunchOptions,
} from "../../../common/types";
import {
  getLauncherCores,
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

const LAUNCH_LOAD_DEFAULT = 22;

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

  const cores = usePromiseWithSnackbarError(() => getLauncherCores(), {
    errorMessage: t("study.error.launcherCores"),
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
          .join(" ")
          .trim(),
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
        sx: { width: "600px", height: "550px", p: 0, overflow: "hidden" },
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
            gap: 2,
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
            }}
          />
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
            }}
            helperText={t("study.timeLimitHelper", {
              max: 240,
            })}
          />
          <UsePromiseCond
            response={cores}
            ifResolved={(cores) => (
              <TextField
                id="nb-cpu"
                label="Number of cores"
                type="number"
                variant="filled"
                defaultValue={cores.defaultValue}
                onChange={(e) =>
                  handleChange("nb_cpu", parseInt(e.target.value, 10))
                }
              />
            )}
            ifPending={() => <Skeleton />}
            ifRejected={() => (
              <TextField disabled variant="filled" size="small" />
            )}
          />
        </Box>
        <Divider
          sx={{ width: 1, mt: 1, border: "0.5px solid", opacity: 0.6 }}
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
            list={launcherVersions}
            data={solverVersion}
            setValue={setSolverVersion}
            sx={{ width: 1, mt: 2 }}
          />
          <TextField
            id="other-options"
            label={t("study.otherOptions")}
            type="text"
            variant="filled"
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
          sx={{ width: 1, my: 1, border: "0.5px solid", opacity: 0.6 }}
          orientation="horizontal"
        />
        <Typography sx={{ mt: 1 }}>Xpansion</Typography>
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
              gap: 2,
              alignItems: "center",
            }}
          >
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
          </Box>
          {outputList && outputList.length === 1 && (
            <Box sx={{ display: "flex", gap: 2 }}>
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
        </FormGroup>
        <Divider
          sx={{ width: 1, my: 1, border: "0.5px solid", opacity: 0.6 }}
          orientation="horizontal"
        />
      </Box>
    </BasicDialog>
  );
}

export default LauncherDialog;
