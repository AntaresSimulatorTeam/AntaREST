import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { genTsOptions, lawOptions, noDataValues, ThermalType } from "./utils";
import { StudyMetadata } from "../../../../../../../common/types";
import ThermalMatrixView from "./ThermalMatrixView";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import { saveField } from "../common/utils";
import { transformNameToId } from "../../../../../../../services/utils";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}

export default function ThermalForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const [t] = useTranslation();
  const pathPrefix = useMemo(
    () => `input/thermal/clusters/${area}/list/${cluster}`,
    [area, cluster]
  );
  const studyId = study.id;

  const groupOptions = useMemo(
    () => groupList.map((item) => ({ label: item, value: item })),
    [groupList]
  );

  const saveValue = useMemo(
    () => saveField(studyId, pathPrefix, noDataValues),
    [pathPrefix, studyId]
  );

  const jsonGenerator: IFormGenerator<ThermalType> = useMemo(
    () => [
      {
        translationId: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            label: t("global.name"),
            path: `${pathPrefix}/name`,
            disabled: true,
          },
          {
            type: "select",
            name: "group",
            label: t("study.modelization.clusters.group"),
            path: `${pathPrefix}/group`,
            options: groupOptions,
          },
        ],
      },
      {
        translationId: "study.modelization.clusters.operatingParameters",
        fields: [
          {
            type: "switch",
            name: "enabled",
            path: `${pathPrefix}/enabled`,
            label: t("study.modelization.clusters.enabled"),
          },
          {
            type: "switch",
            name: "must-run",
            path: `${pathPrefix}/must-run`,
            label: t("study.modelization.clusters.mustRun"),
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
          {
            type: "number",
            name: "min-stable-power",
            path: `${pathPrefix}/min-stable-power`,
            label: t("study.modelization.clusters.minStablePower"),
          },
          {
            type: "number",
            name: "spinning",
            path: `${pathPrefix}/spinning`,
            label: t("study.modelization.clusters.spinning"),
          },
          {
            type: "number",
            name: "min-up-time",
            path: `${pathPrefix}/min-up-time`,
            label: t("study.modelization.clusters.minUpTime"),
          },
          {
            type: "number",
            name: "min-down-time",
            path: `${pathPrefix}/min-down-time`,
            label: t("study.modelization.clusters.minDownTime"),
          },
          {
            type: "number",
            name: "co2",
            path: `${pathPrefix}/co2`,
            label: t("study.modelization.clusters.co2"),
          },
        ],
      },
      {
        translationId: "study.modelization.clusters.operatingCosts",
        fields: [
          {
            type: "number",
            name: "marginal-cost",
            path: `${pathPrefix}/marginal-cost`,
            label: t("study.modelization.clusters.marginalCost"),
          },
          {
            type: "number",
            name: "fixed-cost",
            path: `${pathPrefix}/fixed-cost`,
            label: t("study.modelization.clusters.fixedCost"),
          },
          {
            type: "number",
            name: "startup-cost",
            path: `${pathPrefix}/startup-cost`,
            label: t("study.modelization.clusters.startupCost"),
          },
          {
            type: "number",
            name: "market-bid-cost",
            path: `${pathPrefix}/market-bid-cost`,
            label: t("study.modelization.clusters.marketBidCost"),
          },
          {
            type: "number",
            name: "spread-cost",
            path: `${pathPrefix}/spread-cost`,
            label: t("study.modelization.clusters.spreadCost"),
          },
        ],
      },

      {
        translationId: "study.modelization.clusters.timeSeriesGen",
        fields: [
          {
            type: "select",
            name: "gen-ts",
            path: `${pathPrefix}/gen-ts`,
            label: t("study.modelization.clusters.genTs"),
            options: genTsOptions,
          },
          {
            type: "number",
            name: "volatility.forced",
            path: `${pathPrefix}/volatility.forced`,
            label: t("study.modelization.clusters.volatilityForced"),
          },
          {
            type: "number",
            name: "volatility.planned",
            path: `${pathPrefix}/volatility.planned`,
            label: t("study.modelization.clusters.volatilityPlanned"),
          },
          {
            type: "select",
            name: "law.forced",
            path: `${pathPrefix}/law.forced`,
            label: t("study.modelization.clusters.lawForced"),
            options: lawOptions,
          },
          {
            type: "select",
            name: "law.planned",
            path: `${pathPrefix}/law.planned`,
            label: t("study.modelization.clusters.lawPlanned"),
            options: lawOptions,
          },
        ],
      },
    ],
    [t, pathPrefix, groupOptions]
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
        <ThermalMatrixView
          study={study}
          area={area}
          cluster={transformNameToId(cluster)}
        />
      </Box>
    </>
  );
}
