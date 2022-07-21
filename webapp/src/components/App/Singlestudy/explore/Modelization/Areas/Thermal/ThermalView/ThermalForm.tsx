import * as R from "ramda";
import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import { useFormContext } from "../../../../../../../common/Form";
import { getThermalPath, ThermalFields } from "./utils";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import { StudyMetadata } from "../../../../../../../../common/types";
import SelectFE, {
  SelectFEProps,
} from "../../../../../../../common/fieldEditors/SelectFE";
import ThermalMatrixView from "./ThermalMatrixView";
import { StyledFieldset } from "./style";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}

export default function ThermalForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const [t] = useTranslation();
  const { control, defaultValues } = useFormContext<ThermalFields>();
  const path = useMemo(() => {
    return getThermalPath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const genTsOptions = [
    "use global parameter",
    "force no generation",
    "force generation",
  ].map((item) => ({ label: item, value: item }));

  const groupOptions = groupList.map((item) => ({ label: item, value: item }));

  const lawOptions = ["uniform", "geometric"].map((item) => ({
    label: item,
    value: item,
  }));

  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const saveValue = R.curry((name: string, defaultValue: any, data: any) => {
    if (data === defaultValue || data === undefined) {
      const tmpValues = { ...defaultValues };
      if (name in tmpValues) delete tmpValues[name];
      return editStudy(tmpValues, studyId, pathPrefix);
    }
    return editStudy(data, studyId, path[name]);
  });

  const renderSelect = (name: string, options: SelectFEProps["options"]) => (
    <SelectFE
      name={name}
      label={t(`study.modelization.clusters.${name}`)}
      options={options}
      control={control}
      rules={{
        onAutoSubmit: saveValue(name, options.length > 0 ? options[0] : ""),
      }}
    />
  );

  return (
    <>
      <StyledFieldset legend={t("global.general")}>
        <StringFE
          name="name"
          label={t("global.name")}
          variant="filled"
          control={control}
          rules={{ onAutoSubmit: saveValue("name", "") }}
        />
        {renderSelect("group", groupOptions)}
      </StyledFieldset>
      <StyledFieldset
        legend={t("study.modelization.clusters.operatingParameters")}
      >
        <SwitchFE
          name="enabled"
          label={t("study.modelization.clusters.enabled")}
          control={control}
          rules={{ onAutoSubmit: saveValue("enabled", true) }}
        />
        <SwitchFE
          name="mustRun"
          label={t("study.modelization.clusters.mustRun")}
          control={control}
          rules={{ onAutoSubmit: saveValue("mustRun", false) }}
        />
        <NumberFE
          name="unitcount"
          label={t("study.modelization.clusters.unitcount")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("unitcount", 0),
          }}
        />
        <NumberFE
          name="nominalCapacity"
          label={t("study.modelization.clusters.nominalCapacity")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("nominalCapacity", 0),
          }}
        />
        <NumberFE
          name="minStablePower"
          label={t("study.modelization.clusters.minStablePower")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("minStablePower", 0),
          }}
        />
        <NumberFE
          name="minStablePower"
          label={t("study.modelization.clusters.spinning")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("spinning", 0),
          }}
        />
        <NumberFE
          name="minUpTime"
          label={t("study.modelization.clusters.minUpTime")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("minUpTime", 1),
          }}
        />
        <NumberFE
          name="minDownTime"
          label={t("study.modelization.clusters.minDownTime")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("minDownTime", 1),
          }}
        />
        <NumberFE
          name="co2"
          label={t("study.modelization.clusters.co2")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("co2", 1),
          }}
        />
      </StyledFieldset>
      <StyledFieldset legend={t("study.modelization.clusters.operatingCosts")}>
        <NumberFE
          name="marginalCost"
          label={t("study.modelization.clusters.marginalCost")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("marginalCost", 0),
          }}
        />
        <NumberFE
          name="fixedCost"
          label={t("study.modelization.clusters.fixedCost")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("fixedCost", 0),
          }}
        />
        <NumberFE
          name="startupCost"
          label={t("study.modelization.clusters.startupCost")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("startupCost", 0),
          }}
        />
        <NumberFE
          name="marketBidCost"
          label={t("study.modelization.clusters.marketBidCost")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("marketBidCost", 0),
          }}
        />
        <NumberFE
          name="spreadCost"
          label={t("study.modelization.clusters.spreadCost")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("spreadCost", 0),
          }}
        />
      </StyledFieldset>
      <StyledFieldset legend={t("study.modelization.clusters.timeSeriesGen")}>
        {renderSelect("genTs", genTsOptions)}
        <NumberFE
          name="volatilityForced"
          label={t("study.modelization.clusters.volatilityForced")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("volatilityForced", 0),
          }}
        />
        <NumberFE
          name="volatilityPlanned"
          label={t("study.modelization.clusters.volatilityPlanned")}
          variant="filled"
          control={control}
          rules={{
            onAutoSubmit: saveValue("volatilityPlanned", 0),
          }}
        />
        {renderSelect("lawForced", lawOptions)}
        {renderSelect("lawPlanned", lawOptions)}
      </StyledFieldset>
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
