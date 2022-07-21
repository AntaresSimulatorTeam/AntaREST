import { Box } from "@mui/material";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import { getThermalPath, ThermalFields } from "./utils";
import { StudyMetadata } from "../../../../../../../../common/types";
import ThermalMatrixView from "./ThermalMatrixView";
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
    return getThermalPath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const genTsOptions = useMemo(
    () =>
      ["use global parameter", "force no generation", "force generation"].map(
        (item) => ({ label: item, value: item })
      ),
    []
  );

  const groupOptions = useMemo(
    () => groupList.map((item) => ({ label: item, value: item })),
    [groupList]
  );

  const lawOptions = useMemo(
    () =>
      ["uniform", "geometric"].map((item) => ({
        label: item,
        value: item,
      })),
    []
  );

  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;

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

  const jsonGenerator: IFormGenerator<ThermalFields> = useMemo(
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
            type: "switch",
            name: "mustRun",
            label: t("study.modelization.clusters.mustRun"),
            noDataValue: false,
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
          {
            type: "number",
            name: "minStablePower",
            label: t("study.modelization.clusters.minStablePower"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "spinning",
            label: t("study.modelization.clusters.spinning"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "minUpTime",
            label: t("study.modelization.clusters.minUpTime"),
            noDataValue: 1,
          },
          {
            type: "number",
            name: "minDownTime",
            label: t("study.modelization.clusters.minDownTime"),
            noDataValue: 1,
          },
          {
            type: "number",
            name: "co2",
            label: t("study.modelization.clusters.co2"),
            noDataValue: 0,
          },
        ],
      },
      {
        translationId: "study.modelization.clusters.operatingCosts",
        fields: [
          {
            type: "number",
            name: "marginalCost",
            label: t("study.modelization.clusters.marginalCost"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "fixedCost",
            label: t("study.modelization.clusters.fixedCost"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "startupCost",
            label: t("study.modelization.clusters.startupCost"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "marketBidCost",
            label: t("study.modelization.clusters.marketBidCost"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "spreadCost",
            label: t("study.modelization.clusters.spreadCost"),
            noDataValue: 1,
          },
        ],
      },

      {
        translationId: "study.modelization.clusters.timeSeriesGen",
        fields: [
          {
            type: "select",
            name: "genTs",
            label: t("study.modelization.clusters.genTs"),
            options: genTsOptions,
            noDataValue: genTsOptions[0],
          },
          {
            type: "number",
            name: "volatilityForced",
            label: t("study.modelization.clusters.volatilityForced"),
            noDataValue: 0,
          },
          {
            type: "number",
            name: "volatilityPlanned",
            label: t("study.modelization.clusters.volatilityPlanned"),
            noDataValue: 0,
          },
          {
            type: "select",
            name: "lawForced",
            label: t("study.modelization.clusters.lawForced"),
            options: lawOptions,
            noDataValue: lawOptions[0],
          },
          {
            type: "select",
            name: "lawPlanned",
            label: t("study.modelization.clusters.lawPlanned"),
            options: lawOptions,
            noDataValue: lawOptions[0],
          },
        ],
      },
    ],
    [genTsOptions, t, groupOptions, lawOptions]
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
        <ThermalMatrixView study={study} area={area} cluster={cluster} />
      </Box>
    </>
  );
}
