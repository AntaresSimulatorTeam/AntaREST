import { Box } from "@mui/material";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import { getRenewablePath, RenewableFields } from "./utils";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import MatrixInput from "../../../../../../../common/MatrixInput";
import { IFormGenerator } from "../../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../../common/FormGenerator/AutoSubmitGenerator";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}
export default function ThermalForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const [t] = useTranslation();
  const path = useMemo(() => {
    return getRenewablePath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const tsModeOptions = useMemo(
    () =>
      ["power generation", "production factor"].map((item) => ({
        label: item,
        value: item,
      })),
    []
  );
  const groupOptions = useMemo(
    () => groupList.map((item) => ({ label: item, value: item })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(groupList)]
  );
  const pathPrefix = `input/renewables/clusters/${area}/list/${cluster}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const saveValue = useCallback(
    (defaultValues: any, noDataValue: any, name: string, data: any) => {
      if (data === noDataValue || data === undefined) {
        const tmpValues = { ...defaultValues };
        if (name in tmpValues) delete tmpValues[name];
        return editStudy(tmpValues, studyId, pathPrefix);
      }
      return editStudy(data, studyId, path[name]);
    },
    [path, pathPrefix, studyId]
  );

  const jsonGenerator: IFormGenerator<RenewableFields> = useMemo(
    () => [
      {
        translationId: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            label: t("global.name"),
          },
          {
            type: "select",
            name: "group",
            label: t("study.modelization.clusters.group"),
            options: groupOptions,
            noDataValue: groupOptions[0],
          },
          {
            type: "select",
            name: "tsInterpretation",
            label: t("study.modelization.clusters.tsInterpretation"),
            options: tsModeOptions,
            noDataValue: tsModeOptions[0],
          },
        ],
      },
      {
        translationId: "study.modelization.clusters.operatingParameters",
        fields: [
          {
            type: "switch",
            name: "enabled",
            label: t("study.modelization.clusters.enabled"),
            noDataValue: true,
          },
          {
            type: "number",
            name: "unitcount",
            label: t("study.modelization.clusters.unitcount"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "nominalCapacity",
            label: t("study.modelization.clusters.nominalCapacity"),
            noDataValue: 0,
          },
        ],
      },
    ],
    [groupOptions, t, tsModeOptions]
  );

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={saveValue}
      />
      <Box
        sx={{
          width: "100%",
          display: "flex",
          flexDirection: "column",
          height: "500px",
        }}
      >
        <MatrixInput
          study={study}
          url={`input/renewables/series/${area}/${cluster}/series`}
          computStats={MatrixStats.NOCOL}
        />
      </Box>
    </>
  );
}
