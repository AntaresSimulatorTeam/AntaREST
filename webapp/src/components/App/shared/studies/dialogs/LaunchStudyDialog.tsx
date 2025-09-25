/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import LinearProgressWithLabel from "@/components/common/LinearProgressWithLabel";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import UsePromiseCond from "@/components/common/utils/UsePromiseCond";
import { toError } from "@/utils/fnUtils";
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
import { useSnackbar } from "notistack";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { shallowEqual } from "react-redux";
import { useInterval, useMountedState } from "react-use";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getStudy } from "../../../../../redux/selectors";
import {
  getLauncherMetrics,
  getLaunchersConfig,
  getLauncherVersions,
  getStudyOutputs,
  launchStudy,
} from "../../../../../services/api/study";
import { convertVersions } from "../../../../../services/utils";
import type { LaunchOptions, StudyMetadata, StudyOutput } from "../../../../../types/types";
import SelectSingle from "../../../../common/SelectSingle";
import BasicDialog from "../../../../common/dialogs/BasicDialog";
import CheckBoxFE from "../../../../common/fieldEditors/CheckBoxFE";
import SwitchFE from "../../../../common/fieldEditors/SwitchFE";

interface Props {
  open: boolean;
  studyIds: Array<StudyMetadata["id"]>;
  onClose: () => void;
}

function LaunchStudyDialog(props: Props) {
  const { studyIds, open, onClose } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [options, setOptions] = useState<LaunchOptions>({ auto_unzip: true });
  const [solverVersion, setSolverVersion] = useState<string>();
  const [isLaunching, setIsLaunching] = useState(false);
  const isMounted = useMountedState();

  const studyNames = useAppSelector(
    (state) => studyIds.map((sid) => getStudy(state, sid)?.name),
    shallowEqual,
  );

  const launchersConfigRes = usePromiseWithSnackbarError(
    async () => {
      const config = await getLaunchersConfig();

      return {
        ...config,
        launchersById: R.indexBy(R.prop("id"), config.launchers),
        launcherOptions: config.launchers.map(({ id, name }) => ({ value: id, label: name })),
      };
    },
    {
      errorMessage: t("study.error.launchers"),
      onDataChange: (launchersConfig) => {
        const defaultLauncher = launchersConfig?.launchersById[launchersConfig.defaultLauncher];

        setOptions((prev) => ({
          ...prev,
          launcher_id: defaultLauncher?.id || "",
          nb_cpu: defaultLauncher?.nbCores?.default,
        }));
      },
    },
  );

  const launcherMetricsRes = usePromiseWithSnackbarError(
    () => getLauncherMetrics(options.launcher_id),
    {
      errorMessage: t("study.error.launchLoad"),
      deps: [options.launcher_id],
    },
  );

  // Refresh launcher metrics every minute
  useInterval(launcherMetricsRes.reload, 60_000);

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
      Promise.all(studyIds.map((sid) => launchStudy(sid, options, solverVersion)))
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
          enqueueErrorSnackbar(t("studies.error.runStudy"), toError(err));
        })
        .finally(() => {
          if (isMounted()) {
            setIsLaunching(false);
          }
        });
    }
  };

  const handleChange = <T extends keyof LaunchOptions>(field: T, value: LaunchOptions[T]) => {
    setOptions((prevOptions) => ({
      ...prevOptions,
      [field]: value,
    }));
  };

  const handleObjectChange = <T extends keyof LaunchOptions>(field: T, value: object) => {
    setOptions((prevOptions: LaunchOptions) => {
      return {
        ...prevOptions,
        [field]: { ...(prevOptions[field] as object), ...value },
      };
    });
  };

  const handleOtherOptionsChange = (optionChanges: Array<{ option: string; active: boolean }>) => {
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
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("study.runStudy")}
      open={open}
      onClose={onClose}
      maxWidth="md"
      slotProps={{ paper: { sx: { width: 700 } } }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            disabled={isLaunching || !launchersConfigRes.isFulfilled}
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
        <TextField
          label={t("global.name")}
          type="text"
          variant="outlined"
          value={options.output_suffix}
          onChange={(e) => handleChange("output_suffix", e.target.value.trim())}
          slotProps={{
            inputLabel: {
              shrink: true,
            },
          }}
        />
        <Divider
          sx={{ width: 1, mt: 2, mb: 1, border: "0.5px solid", opacity: 0.7 }}
          orientation="horizontal"
        />
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            width: 1,
            mt: 1,
          }}
        >
          <Typography>Simulateur</Typography>
          <SelectSingle
            name={t("global.version")}
            variant="outlined"
            list={launcherVersions}
            data={solverVersion}
            setValue={setSolverVersion}
            sx={{ flex: 1 }}
          />
          <TextField
            label={t("study.otherOptions")}
            type="text"
            variant="outlined"
            value={options.other_options}
            onChange={(e) => handleChange("other_options", e.target.value)}
            sx={{ flex: 1 }}
            slotProps={{
              inputLabel: {
                shrink: true,
              },
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
            onChange={(_e, checked) =>
              handleOtherOptionsChange([{ option: "xpress", active: checked }])
            }
          />
          <CheckBoxFE
            label={t("launcher.autoUnzip")}
            value={!!options.auto_unzip}
            onChange={(_e, checked) => handleChange("auto_unzip", checked)}
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
              onChange={(_e, checked) => {
                handleChange("xpansion", checked ? { enabled: true } : undefined);
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
                    onChange={(_e, checked) =>
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
                setValue={(data) =>
                  handleObjectChange("xpansion", {
                    output_id: data,
                  })
                }
                sx={{ minWidth: 400 }}
              />
            </Box>
          )}
        </FormGroup>
        <Divider
          sx={{ width: 1, my: 2, border: "0.5px solid", opacity: 0.7 }}
          orientation="horizontal"
        />
        <Box
          sx={{
            display: "flex",
            gap: 2,
            alignItems: "center",
          }}
        >
          <UsePromiseCond
            response={launchersConfigRes}
            ifFulfilled={({ launchersById, launcherOptions }) => {
              const currentLauncher = launchersById[options.launcher_id || ""];
              const nbCores = currentLauncher?.nbCores;
              const minCores = nbCores?.min;
              const maxCores = nbCores?.max;

              return (
                <>
                  <SelectFE
                    label={t("study.cluster")}
                    value={options.launcher_id}
                    options={launcherOptions}
                    onChange={(e) => {
                      const newLauncherId = e.target.value;

                      setOptions((prev) => ({
                        ...prev,
                        launcher_id: newLauncherId,
                        nb_cpu: launchersById[newLauncherId]?.nbCores.default,
                      }));
                    }}
                    sx={{ flex: 1 }}
                  />

                  <TextField
                    label={t("study.nbCpu")}
                    type="number"
                    variant="outlined"
                    value={options.nb_cpu}
                    onChange={(e) => {
                      handleChange("nb_cpu", R.clamp(minCores, maxCores, Number(e.target.value)));
                    }}
                    slotProps={{
                      htmlInput: {
                        min: minCores,
                        max: maxCores,
                        step: 1,
                      },
                    }}
                    sx={{ width: 150 }}
                  />

                  {/* Field only to display the value, it is not editable */}
                  <TextField
                    label={t("study.timeLimit")}
                    type="number"
                    variant="outlined"
                    disabled
                    value={currentLauncher?.timeLimit.default}
                    slotProps={{
                      inputLabel: {
                        shrink: true,
                      },
                    }}
                    sx={{ width: 150 }}
                  />
                </>
              );
            }}
            ifPending={() => <Skeleton height={60} sx={{ flex: 1 }} />}
            ifRejected={() => <Skeleton height={60} sx={{ flex: 1 }} />}
          />
        </Box>
        <Box
          sx={{
            display: "flex",
            alignContent: "center",
            gap: 1,
            mt: 2,
          }}
        >
          <UsePromiseCond
            // Reload when launcher changes to see Skeleton
            // because `keepLastResolvedOnReload` is set to true for refresh
            key={options.launcher_id}
            response={launcherMetricsRes}
            keepLastResolvedOnReload
            ifPending={() => <Skeleton width={500} />}
            ifFulfilled={(data) => (
              <>
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.allocatedCpuRate")}
                </Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.allocatedCpuRate)}
                  tooltip={t("study.allocatedCpuRate")}
                  sx={{ width: 100 }}
                  colorMode="cluster"
                />
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.clusterLoadRate")}
                </Typography>
                <LinearProgressWithLabel
                  value={Math.floor(data.clusterLoadRate)}
                  tooltip={t("study.clusterLoadRate")}
                  sx={{ width: 100 }}
                  colorMode="cluster"
                />
                <Typography fontSize="small" sx={{ textWrap: "nowrap" }}>
                  {t("study.nbQueuedJobs")}: {data.nbQueuedJobs}
                </Typography>
              </>
            )}
          />
        </Box>
      </Box>
    </BasicDialog>
  );
}

export default LaunchStudyDialog;
