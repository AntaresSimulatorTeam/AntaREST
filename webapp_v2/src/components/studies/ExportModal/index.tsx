import { ReactNode, useEffect, useState } from "react";
import * as R from "ramda";
import { AxiosError } from "axios";
import { Box, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import debug from "debug";
import _ from "lodash";
import {
  FileStudyTreeConfigDTO,
  GenericInfo,
  StudyMetadata,
  StudyOutput,
  StudyOutputDownloadDTO,
  StudyOutputDownloadLevelDTO,
  StudyOutputDownloadType,
} from "../../../common/types";
import BasicDialog, {
  BasicDialogProps,
} from "../../common/dialogs/BasicDialog";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import SelectSingle from "../../common/SelectSingle";
import {
  exportStudy,
  exportOuput as callExportOutput,
  getStudyOutputs,
  getStudySynthesis,
  downloadOutput,
} from "../../../services/api/study";
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

  const optionsList: Array<GenericInfo> = [
    {
      id: "exportWith",
      name: t("studymanager:exportWith"),
    },
    {
      id: "exportWithout",
      name: t("studymanager:exportWithout"),
    },
    {
      id: "exportOutput",
      name: t("studymanager:exportOutput"),
    },
    {
      id: "exportOutputFilter",
      name: t("studymanager:exportOutputFilter"),
    },
  ];
  const [optionSelection, setOptionSelection] = useState<string>("exportWith");
  const [outputList, setOutputList] = useState<Array<GenericInfo>>();
  const [currentOutput, setCurrentOutput] = useState<string>();
  const [synthesis, setStudySynthesis] = useState<FileStudyTreeConfigDTO>();
  const [filter, setFilter] = useState<StudyOutputDownloadDTO>({
    type: StudyOutputDownloadType.AREA,
    level: StudyOutputDownloadLevelDTO.WEEKLY,
    synthesis: false,
    includeClusters: false,
  });

  const exportOutput = _.debounce(
    async (output: string) => {
      if (study) {
        try {
          await callExportOutput(study.id, output);
        } catch (e) {
          enqueueErrorSnackbar(
            t("singlestudy:failedToExportOutput"),
            e as AxiosError
          );
        }
      }
    },
    2000,
    { leading: true, trailing: false }
  );

  const onExportFiltered = async (
    output: string,
    filter: StudyOutputDownloadDTO
  ): Promise<void> => {
    if (study) {
      try {
        await downloadOutput(study.id, output, filter);
        enqueueSnackbar(t("singlestudy:outputExportInProgress"), {
          variant: "info",
        });
      } catch (e) {
        enqueueErrorSnackbar(
          t("singlestudy:failedToExportOutput"),
          e as AxiosError
        );
      }
    }
  };

  const onExportClick = (): void => {
    if (optionSelection === "exportOutput") {
      if (currentOutput) exportOutput(currentOutput);
      return;
    }
    if (optionSelection === "exportOutputFilter") {
      if (currentOutput) onExportFiltered(currentOutput, filter);
      return;
    }
    exportStudy(study.id, optionSelection === "exportWithout");
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await getStudyOutputs(study.id);
        const tmpSynth = await getStudySynthesis(study.id);
        setOutputList(
          res.map((o: StudyOutput) => ({ id: o.name, name: o.name }))
        );
        setCurrentOutput(res.length > 0 ? res[0].name : undefined);
        setStudySynthesis(tmpSynth);
      } catch (e) {
        logError(t("singlestudy:failedToListOutputs"), study, e);
      }
    })();
  }, [study, t]);

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("studymanager:export")}
      alert="info"
      actions={
        <Box>
          <Button
            variant="text"
            color="error"
            onClick={onClose ? () => onClose({}, "backdropClick") : undefined}
          >
            {t("main:closeButton")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="info"
            variant="contained"
            onClick={onExportClick}
          >
            {t("main:export")}
          </Button>
        </Box>
      }
    >
      <Box sx={{ p: 2, width: "500px", height: "400px" }}>
        <SelectSingle
          name={`${t("studymanager:exportOptions")} *`}
          list={optionsList}
          data={optionSelection}
          setValue={(data: string) => setOptionSelection(data)}
          sx={{ width: "300px" }}
        />
        {R.cond([
          [
            () =>
              (optionSelection === "exportOutput" ||
                optionSelection === "exportOutputFilter") &&
              outputList !== undefined,
            () =>
              (
                <SelectSingle
                  name={`${t("studymanager:selectOutput")} *`}
                  list={outputList as Array<GenericInfo>}
                  data={currentOutput}
                  setValue={(data: string) => setOptionSelection(data)}
                  sx={{ width: "300px", my: 3 }}
                />
              ) as ReactNode,
          ],
        ])()}
        {R.cond([
          [
            () => optionSelection === "exportOutputFilter",
            // currentOutput !== undefined,
            () =>
              (
                <ExportFilter
                  output={currentOutput as string}
                  synthesis={synthesis}
                  filter={filter}
                  setFilter={setFilter}
                />
              ) as ReactNode,
          ],
        ])()}
      </Box>
    </BasicDialog>
  );
}
