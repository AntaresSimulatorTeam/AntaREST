import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { AllocationFormFields } from "./utils";
import AllocationField from "./AllocationField";
import DynamicList from "../../../../../../../common/DynamicList";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getAreasById } from "../../../../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../../../../common/types";
import { useAreasOptions } from "../hooks/useAreasOptions";

function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const areasById = useAppSelector((state) => getAreasById(state, studyId));
  const { control } = useFormContextPlus<AllocationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "allocation",
  });

  const options = useAreasOptions(fields);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <DynamicList
      items={fields}
      renderItem={(item, index) => (
        <AllocationField
          key={item.id}
          field={item}
          index={index}
          label={areasById?.[item.areaId]?.name}
        />
      )}
      options={options}
      onAdd={(value) =>
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
