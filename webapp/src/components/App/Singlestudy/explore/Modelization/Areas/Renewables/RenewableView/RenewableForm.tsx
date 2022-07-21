import * as R from "ramda";
import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import { useFormContext } from "../../../../../../../common/Form";
import { getRenewablePath, RenewableFields } from "./utils";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import SelectFE, {
  SelectFEProps,
} from "../../../../../../../common/fieldEditors/SelectFE";
import { StyledFieldset } from "./style";
import MatrixInput from "../../../../../../../common/MatrixInput";
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
  const { control, defaultValues } = useFormContext<RenewableFields>();
  const path = useMemo(() => {
    return getRenewablePath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const tsModeOptions = ["power generation", "production factor"].map(
    (item) => ({ label: item, value: item })
  );

  const groupOptions = groupList.map((item) => ({ label: item, value: item }));

  const pathPrefix = `input/renewables/clusters/${area}/list/${cluster}`;

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
        {renderSelect("tsInterpretation", tsModeOptions)}
      </StyledFieldset>
      <StyledFieldset
        legend={t("study.modelization.clusters.operatingParameters")}
        style={{ padding: "16px" }}
      >
        <SwitchFE
          name="enabled"
          label={t("study.modelization.clusters.enabled")}
          control={control}
          rules={{ onAutoSubmit: saveValue("enabled", true) }}
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
      </StyledFieldset>
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
