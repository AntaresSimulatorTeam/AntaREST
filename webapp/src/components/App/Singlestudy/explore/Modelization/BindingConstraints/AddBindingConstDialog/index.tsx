import { useMemo } from "react";
import { Box } from "@mui/material";
import { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import FormDialog from "../../../../../../common/dialogs/FormDialog";
import {
  BindingConstraintOperator,
  TimeStep,
} from "../../../../Commands/Edition/commandTypes";
import { SubmitHandlerPlus } from "../../../../../../common/Form/types";
import { BindingConstFields } from "../BindingConstView/utils";
import { createBindingConstraint } from "../../../../../../../services/api/studydata";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { StudyMetadata } from "../../../../../../../common/types";

interface Props {
  studyId: StudyMetadata["id"];
  existingConstraints: Array<BindingConstFields["id"]>;
  open: boolean;
  onClose: VoidFunction;
}

function AddBindingConstDialog({
  studyId,
  existingConstraints,
  open,
  onClose,
}: Props) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();

  const defaultValues = {
    name: "",
    enabled: true,
    time_step: TimeStep.HOURLY,
    operator: BindingConstraintOperator.LESS,
    coeffs: {},
    comments: "",
  };

  const operatorOptions = useMemo(
    () =>
      ["less", "equal", "greater", "both"].map((item) => ({
        label: t(`study.modelization.bindingConst.operator.${item}`),
        value: item,
      })),
    [t],
  );

  const typeOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (
    data: SubmitHandlerPlus<typeof defaultValues>,
  ) => {
    try {
      await createBindingConstraint(studyId, data.values);
      enqueueSnackbar(t("study.success.addBindingConst"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.addBindingConst"), e as AxiosError);
    } finally {
      onClose();
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      key={studyId}
      title={t("study.modelization.bindingConst.newBindingConst")}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onCancel={onClose}
      open={open}
    >
      {({ control }) => (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          <SwitchFE
            name="enabled"
            label={t("study.modelization.bindingConst.enabled")}
            control={control}
          />
          <StringFE
            name="name"
            label={t("global.name")}
            variant="filled"
            control={control}
            rules={{
              validate: (v) => {
                if (v.trim().length <= 0) {
                  return t("form.field.required");
                }
                if (existingConstraints.includes(v.trim().toLowerCase())) {
                  return t("form.field.duplicate", { 0: v });
                }
              },
            }}
          />
          <SelectFE
            name="time_step"
            label={t("study.modelization.bindingConst.type")}
            options={typeOptions}
            control={control}
          />
          <SelectFE
            name="operator"
            label={t(t("study.modelization.bindingConst.operator"))}
            options={operatorOptions}
            control={control}
          />
        </Box>
      )}
    </FormDialog>
  );
}

export default AddBindingConstDialog;
