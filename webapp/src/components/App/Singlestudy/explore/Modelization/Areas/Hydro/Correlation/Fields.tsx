import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreasById } from "../../../../../../../../redux/selectors";
import DynamicList from "../../../../../../../common/DynamicList";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { useAreasOptions } from "../hooks/useAreasOptions";
import CorrelationField from "./CorrelationField";
import { CorrelationFormFields } from "./utils";

function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areasById = useAppSelector((state) => getAreasById(state, studyId));
  const { control } = useFormContextPlus<CorrelationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "correlation",
  });

  const options = useAreasOptions(fields);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DynamicList
      items={fields}
      renderItem={(item, index) => (
        <CorrelationField
          key={item.id}
          field={item}
          index={index}
          label={areasById?.[item.areaId]?.name}
        />
      )}
      options={options}
      onAdd={(value: string) =>
        append({
          areaId: value,
          coefficient: 0,
        })
      }
      onDelete={remove}
      allowEmpty={false}
    />
  );
}

export default Fields;
