import { AxiosError } from "axios";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import { BindingConstFields, ConstraintType, dataToId } from "./utils";
import {
  AllClustersAndLinks,
  StudyMetadata,
} from "../../../../../../../common/types";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import { ConstraintItem } from "./ConstraintTerm";
import { useFormContext } from "../../../../../../common/Form";
import { updateConstraintTerm } from "../../../../../../../services/api/studydata";
import TextSeparator from "../../../../../../common/TextSeparator";
import { ConstraintHeader, ConstraintList, ConstraintTerm } from "./style";
import AddConstraintTermDialog from "./AddConstraintTermDialog";

interface Props {
  bcIndex: number;
  study: StudyMetadata;
  bindingConst: string;
  options: AllClustersAndLinks;
}

export default function BindingConstForm(props: Props) {
  const { study, options, bindingConst, bcIndex } = props;
  const studyId = study.id;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const { control } = useFormContext<BindingConstFields>();
  const { fields, update, append } = useFieldArray({
    control,
    name: "constraints",
  });

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

  const [addConstraintTermDialog, setAddConstraintTermDialog] = useState(false);

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

  const saveContraintValue = useCallback(
    async (
      index: number,
      prevConst: ConstraintType,
      constraint: Partial<ConstraintType>
    ) => {
      try {
        await updateConstraintTerm(study.id, bindingConst, constraint);
        const tmpConst = prevConst;
        if (constraint.weight !== undefined)
          tmpConst.weight = constraint.weight;
        if (constraint.offset !== undefined)
          tmpConst.offset = constraint.offset;
        if (constraint.data) tmpConst.data = constraint.data;
        tmpConst.id = dataToId(tmpConst.data);
        update(index, tmpConst);
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [bindingConst, enqueueErrorSnackbar, study.id, t, update]
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
        legend={t("study.modelization.bindingConst.constraintTerm")}
        style={{ padding: "16px" }}
      >
        <ConstraintList>
          <ConstraintHeader>
            <Button
              variant="text"
              color="primary"
              onClick={() => setAddConstraintTermDialog(true)}
            >
              {t("study.modelization.bindingConst.addConstraintTerm")}
            </Button>
          </ConstraintHeader>
          {fields.map((field: ConstraintType, index: number) => {
            const constraint = field;
            constraint.id = dataToId(field.data);
            return index > 0 ? (
              <ConstraintTerm key={constraint.id}>
                <TextSeparator
                  text="+"
                  rootStyle={{ my: 0.25 }}
                  textStyle={{ fontSize: "22px" }}
                />
                <ConstraintItem
                  options={options}
                  saveValue={(value) =>
                    saveContraintValue(index, constraint, value)
                  }
                  constraint={constraint}
                />
              </ConstraintTerm>
            ) : (
              <ConstraintItem
                key={constraint.id}
                options={options}
                saveValue={(value) =>
                  saveContraintValue(index, constraint, value)
                }
                constraint={constraint}
              />
            );
          })}
        </ConstraintList>
        {addConstraintTermDialog && (
          <AddConstraintTermDialog
            open={addConstraintTermDialog}
            studyId={studyId}
            bindingConstraint={bindingConst}
            title={t("study.modelization.bindingConst.newBindingConst")}
            onCancel={() => setAddConstraintTermDialog(false)}
            append={append}
          />
        )}
      </Fieldset>
    </>
  );
}
