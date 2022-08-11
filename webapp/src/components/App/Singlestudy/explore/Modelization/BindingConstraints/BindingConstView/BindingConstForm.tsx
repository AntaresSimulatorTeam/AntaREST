import { AxiosError } from "axios";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import { BindingConstFields } from "./utils";
import { StudyMetadata } from "../../../../../../../common/types";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import { Constraints } from "./Constraints";

interface Props {
  bcIndex: number;
  study: StudyMetadata;
  bindingConst: string;
}

export default function BindingConstForm(props: Props) {
  const { study, bindingConst, bcIndex } = props;
  const studyId = study.id;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const pathPrefix = useMemo(
    () => `input/bindingconstraints/bindingconstraints/${bcIndex}`,
    [bcIndex]
  );

  const optionOperator = useMemo(
    () =>
      ["less", "equal", "greater", "both"].map((item) => ({
        label: t(`study.modelization.bindingConst.operator.${item}`),
        value: item.toLowerCase(),
      })),
    [t]
  );

  const typeOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly"].map((item) => ({
        label: t(`study.${item}`),
        value: item,
      })),
    [t]
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const saveValue = useCallback(
    async (name: string, path: string, defaultValues: any, data: any) => {
      try {
        await editStudy(data, studyId, path);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [enqueueErrorSnackbar, studyId, t]
  );

  const jsonGenerator: IFormGenerator<BindingConstFields> = useMemo(
    () => [
      {
        translationId: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            path: `${pathPrefix}/name`,
            label: t("global.name"),
            disabled: true,
            required: t("form.field.required") as string,
          },
          {
            type: "text",
            name: "comments",
            path: `${pathPrefix}/comments`,
            label: t("study.modelization.bindingConst.comments"),
          },
          {
            type: "select",
            name: "time_step",
            path: `${pathPrefix}/type`,
            label: t("study.modelization.bindingConst.type"),
            options: typeOptions,
          },
          {
            type: "select",
            name: "operator",
            path: `${pathPrefix}/operator`,
            label: t("study.modelization.bindingConst.operator"),
            options: optionOperator,
          },
          {
            type: "switch",
            name: "enabled",
            path: `${pathPrefix}/enabled`,
            label: t("study.modelization.bindingConst.enabled"),
          },
        ],
      },
    ],
    [optionOperator, pathPrefix, t, typeOptions]
  );

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={saveValue}
      />
      <Fieldset
        legend={t("study.modelization.bindingConst.constraints")}
        style={{ padding: "16px" }}
      >
        <Constraints bindingConstId={bindingConst} studyId={study.id} />
      </Fieldset>
    </>
  );
}
