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

import { useEffect, useState } from "react";
import * as R from "ramda";
import type { AxiosError } from "axios";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import debug from "debug";
import debounce from "lodash/debounce";
import {
  StudyOutputDownloadLevelDTO,
  StudyOutputDownloadType,
  type FileStudyTreeConfigDTO,
  type GenericInfo,
  type StudyMetadata,
  type StudyOutput,
  type StudyOutputDownloadDTO,
} from "../../../../types/types";
import BasicDialog, { type BasicDialogProps } from "../../../common/dialogs/BasicDialog";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
import SelectSingle from "../../../common/SelectSingle";
import {
  exportStudy,
  exportOutput as callExportOutput,
  getStudyOutputs,
  getStudySynthesis,
  downloadOutput,
} from "../../../../services/api/study";
import ExportFilter from "./ExportFilter";

const logError = debug("antares:studies:card:error");

interface Props {
  study: StudyMetadata;
}

export default function ExportModal(props: BasicDialogProps & Props) {
  const { open, onClose, study } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const optionsList: GenericInfo[] = [
    {
      id: "exportWith",
      name: t("studies.exportWith"),
    },
    {
      id: "exportWithout",
      name: t("studies.exportWithout"),
    },
    {
      id: "exportOutput",
      name: t("studies.exportOutput"),
    },
    {
      id: "exportOutputFilter",
      name: t("studies.exportOutputFilter"),
    },
  ];
  const [optionSelection, setOptionSelection] = useState<string>("exportWith");
  const [outputList, setOutputList] = useState<GenericInfo[]>();
  const [currentOutput, setCurrentOutput] = useState<string>();
  const [studySynthesis, setStudySynthesis] = useState<FileStudyTreeConfigDTO>();
  const [filter, setFilter] = useState<StudyOutputDownloadDTO>({
    type: StudyOutputDownloadType.AREAS,
    level: StudyOutputDownloadLevelDTO.WEEKLY,
    synthesis: false,
    includeClusters: false,
  });

  const exportOutput = debounce(
    async (output: string) => {
      if (study) {
        try {
          await callExportOutput(study.id, output);
        } catch (e) {
          enqueueErrorSnackbar(t("study.error.exportOutput"), e as AxiosError);
        }
      }
    },
    2000,
    { leading: true, trailing: false },
  );

  const onExportFiltered = async (
    output: string,
    filter: StudyOutputDownloadDTO,
  ): Promise<void> => {
    if (study) {
      try {
        await downloadOutput(study.id, output, filter);
        enqueueSnackbar(t("study.message.outputExportInProgress"), {
          variant: "info",
        });
      } catch (e) {
        enqueueErrorSnackbar(t("study.error.exportOutput"), e as AxiosError);
      }
    }
  };

  const onExportClick = (): void => {
    if (onClose) {
      onClose({}, "backdropClick");
    }
    if (optionSelection === "exportOutput") {
      if (currentOutput) {
        exportOutput(currentOutput);
      }
      return;
    }
    if (optionSelection === "exportOutputFilter") {
      if (currentOutput) {
        onExportFiltered(currentOutput, filter);
      }
      return;
    }
    exportStudy(study.id, optionSelection === "exportWithout");
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await getStudyOutputs(study.id);
        const tmpSynth = await getStudySynthesis(study.id);
        setOutputList(res.map((o: StudyOutput) => ({ id: o.name, name: o.name })));
        setCurrentOutput(res.length > 0 ? res[0].name : undefined);
        setStudySynthesis(tmpSynth);
      } catch (e) {
        logError(t("study.error.listOutputs"), study, e);
      }
    })();
  }, [study, t]);

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("global.export")}
      actions={
        <Box>
          <Button
            variant="text"
            color="error"
            onClick={onClose ? () => onClose({}, "backdropClick") : undefined}
          >
            {t("global.close")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="success"
            variant="contained"
            disabled={
              ["exportOutputFilter", "exportOutput"].indexOf(optionSelection) !== -1 &&
              currentOutput === undefined
            }
            onClick={onExportClick}
          >
            {t("global.export")}
          </Button>
        </Box>
      }
    >
      <Box
        sx={{
          p: 2,
        }}
      >
        <SelectSingle
          name={t("studies.exportOptions")}
          list={optionsList}
          data={optionSelection}
          setValue={(data: string) => setOptionSelection(data)}
          sx={{ width: "300px" }}
          required
        />
        {R.cond([
          [
            () =>
              (optionSelection === "exportOutput" || optionSelection === "exportOutputFilter") &&
              outputList !== undefined,
            () =>
              (
                <SelectSingle
                  name={t("studies.selectOutput")}
                  list={outputList as GenericInfo[]}
                  data={currentOutput}
                  setValue={(data: string) => setCurrentOutput(data)}
                  sx={{ width: "300px", my: 3 }}
                  required
                />
              ) as React.ReactNode,
          ],
        ])()}
        {R.cond([
          [
            () => optionSelection === "exportOutputFilter" && currentOutput !== undefined,
            () =>
              (
                <ExportFilter
                  output={currentOutput as string}
                  synthesis={studySynthesis}
                  filter={filter}
                  setFilter={setFilter}
                />
              ) as React.ReactNode,
          ],
        ])()}
      </Box>
    </BasicDialog>
  );
}
