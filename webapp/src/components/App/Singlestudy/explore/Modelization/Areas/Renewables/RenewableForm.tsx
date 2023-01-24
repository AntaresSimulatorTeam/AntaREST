import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { noDataValues, RenewableType, tsModeOptions } from "./utils";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import MatrixInput from "../../../../../../common/MatrixInput";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import { saveField } from "../common/utils";
import { transformNameToId } from "../../../../../../../services/utils";
import DocLink from "../../../../../../common/DocLink";
import { ACTIVE_WINDOWS_DOC_PATH } from "../../BindingConstraints/BindingConstView/utils";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}

export default function RenewableForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const [t] = useTranslation();
  const pathPrefix = useMemo(
    () => `input/renewables/clusters/${area}/list/${cluster}`,
    [area, cluster]
  );
  const studyId = study.id;

  const groupOptions = useMemo(
    () => groupList.map((item) => ({ label: item, value: item })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(groupList)]
  );

  const saveValue = useMemo(
    () => saveField(studyId, pathPrefix, noDataValues),
    [pathPrefix, studyId]
  );

  const jsonGenerator: IFormGenerator<RenewableType> = useMemo(
    () => [
      {
        legend: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            path: `${pathPrefix}/name`,
            label: t("global.name"),
            disabled: true,
          },
          {
            type: "select",
            name: "group",
            path: `${pathPrefix}/group`,
            label: t("study.modelization.clusters.group"),
            options: groupOptions,
          },
          {
            type: "select",
            name: "ts-interpretation",
            path: `${pathPrefix}/ts-interpretation`,
            label: t("study.modelization.clusters.tsInterpretation"),
            options: tsModeOptions,
          },
        ],
      },
      {
        legend: "study.modelization.clusters.operatingParameters",
        fields: [
          {
            type: "switch",
            name: "enabled",
            path: `${pathPrefix}/enabled`,
            label: t("study.modelization.clusters.enabled"),
          },
          {
            type: "number",
            name: "unitcount",
            path: `${pathPrefix}/unitcount`,
            label: t("study.modelization.clusters.unitcount"),
          },
          {
            type: "number",
            name: "nominalcapacity",
            path: `${pathPrefix}/nominalcapacity`,
            label: t("study.modelization.clusters.nominalCapacity"),
          },
        ],
      },
    ],
    [groupOptions, pathPrefix, t]
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
        <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#renewable`} isAbsolute />
        <MatrixInput
          study={study}
          url={`input/renewables/series/${area}/${transformNameToId(
            cluster
          )}/series`}
          computStats={MatrixStats.NOCOL}
        />
      </Box>
    </>
  );
}
