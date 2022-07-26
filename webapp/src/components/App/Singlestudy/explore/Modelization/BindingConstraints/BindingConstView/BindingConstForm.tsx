import { AxiosError } from "axios";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import { getBindingConstPath, BindingConstFields } from "./utils";
import { StudyMetadata } from "../../../../../../../common/types";
import { Content } from "../style";
import Constraint from "./Constraint";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";

interface Props {
  bcIndex: number;
  study: StudyMetadata;
}

export default function BindingConstForm(props: Props) {
  const { study, bcIndex } = props;
  const studyId = study.id;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const path = useMemo(() => {
    return getBindingConstPath(bcIndex);
  }, [bcIndex]);

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
    async (defaultValues: any, defaultValue: any, name: string, data: any) => {
      try {
        console.log("IT'S WORKING");
        await editStudy(data, studyId, path[name]);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [enqueueErrorSnackbar, path, studyId, t]
  );

  const jsonGenerator: IFormGenerator<BindingConstFields> = useMemo(
    () => [
      {
        translationId: "global.general",
        fields: [
          {
            type: "text",
            name: "name",
            label: t("global.name"),
            required: t("form.field.required") as string,
          },
          {
            type: "text",
            name: "comments",
            label: t("study.modelization.bindingConst.comments"),
          },
          {
            type: "select",
            name: "type",
            label: t("study.modelization.bindingConst.type"),
            options: typeOptions,
          },
          {
            type: "select",
            name: "operator",
            label: t("study.modelization.bindingConst.operator"),
            options: optionOperator,
          },
          {
            type: "switch",
            name: "enabled",
            label: t("study.modelization.bindingConst.enabled"),
          },
        ],
      },
    ],
    [optionOperator, t, typeOptions]
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
        <Content>
          <Constraint areaList={[]} />
        </Content>
      </Fieldset>
    </>
  );
}
