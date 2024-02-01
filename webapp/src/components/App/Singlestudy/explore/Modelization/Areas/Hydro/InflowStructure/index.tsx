import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import Form from "../../../../../../../common/Form";
import {
  type InflowStructureFields,
  getInflowStructureFields,
  updateInflowStructureFields,
} from "./utils";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { useTranslation } from "react-i18next";

function InflowStructure() {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<InflowStructureFields>) => {
    return updateInflowStructureFields(study.id, areaId, data.values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Form
      key={study.id + areaId}
      config={{
        defaultValues: () => getInflowStructureFields(study.id, areaId),
      }}
      onSubmit={handleSubmit}
      miniSubmitButton
      enableUndoRedo
      sx={{ display: "flex", alignItems: "center", ".Form__Footer": { p: 0 } }}
    >
      {({ control }) => (
        <NumberFE
          label="Inter-Monthly Correlation"
          name="interMonthlyCorrelation"
          control={control}
          rules={{
            min: {
              value: 0,
              message: t("form.field.minValue", { 0: 0 }),
            },
            max: {
              value: 1,
              message: t("form.field.maxValue", { 0: 1 }),
            },
          }}
          inputProps={{ step: 0.1 }}
          size="small"
          sx={{ width: 180 }}
        />
      )}
    </Form>
  );
}

export default InflowStructure;
