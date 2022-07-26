import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  getRenewablePath,
  RenewableFields,
  saveField,
  tsModeOptions,
} from "./utils";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}

export default function RenewableForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const [t] = useTranslation();
  const [path, pathPrefix] = useMemo(() => {
    return [
      getRenewablePath(area, cluster),
      `input/renewables/clusters/${area}/list/${cluster}`,
    ];
  }, [area, cluster]);
  const studyId = study.id;

  const groupOptions = useMemo(
    () => groupList.map((item) => ({ label: item, value: item })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(groupList)]
  );

  const saveValue = useMemo(
    () => saveField(studyId, pathPrefix, path),
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
    [groupOptions, t]
  );

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={saveValue}
      />
      <Box
        sx={{
          width: 1,
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
