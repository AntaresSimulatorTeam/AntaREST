import { useMemo } from "react";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import FormDialog from "../../../../../common/dialogs/FormDialog";
import {
  BindingConstraintOperator,
  TimeStep,
} from "../../../Commands/Edition/commandTypes";
import { SubmitHandlerPlus } from "../../../../../common/Form/types";
import { BindingConstFields } from "./BindingConstView/utils";
import { createBindingConstraint } from "../../../../../../services/api/studydata";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import { StudyMetadata } from "../../../../../../common/types";
import { validateString } from "../../../../../../utils/validationUtils";

interface Props {
  studyId: StudyMetadata["id"];
  existingConstraints: Array<BindingConstFields["id"]>;
  open: boolean;
  onClose: VoidFunction;
}

function AddDialog({ studyId, existingConstraints, open, onClose }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const defaultValues = {
    name: "",
    enabled: true,
    time_step: TimeStep.HOURLY,
    operator: BindingConstraintOperator.LESS,
    comments: "",
    coeffs: {},
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
    return createBindingConstraint(studyId, data.values);
  };

  const handleSubmitSuccessful = () => {
    enqueueSnackbar(t("study.success.addBindingConst"), {
      variant: "success",
    });
    onClose();
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
      onSubmitSuccessful={handleSubmitSuccessful}
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
            control={control}
            rules={{
              validate: (v) =>
                validateString(v, { existingValues: existingConstraints }),
            }}
          />
          <StringFE
            name="comments"
            label={t("study.modelization.bindingConst.comments")}
            control={control}
          />
          <SelectFE
            name="time_step"
            label={t("study.modelization.bindingConst.type")}
            variant="outlined"
            options={typeOptions}
            control={control}
          />
          <SelectFE
            name="operator"
            label={t(t("study.modelization.bindingConst.operator"))}
            variant="outlined"
            options={operatorOptions}
            control={control}
          />
        </Box>
      )}
    </FormDialog>
  );
}

export default AddDialog;
