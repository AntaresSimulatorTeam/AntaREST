import { Divider, Grid } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import { useFormContextPlus } from "../../../../../../../common/Form";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getStudySynthesis,
} from "../../../../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../../../../common/types";
import { AllocationFormFields } from "./utils";
import AllocationSelect from "./AllocationSelect";
import AllocationField from "./AllocationField";

function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const { control } = useFormContextPlus<AllocationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "allocation",
  });
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const areasById = useAppSelector(
    (state) => getStudySynthesis(state, studyId)?.areas
  );

  const filteredAreas = useMemo(() => {
    const allocatedAreaIds = fields.map((field) => field.areaId);
    return areas.filter((area) => !allocatedAreaIds.includes(area.id));
  }, [areas, fields]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getAreaLabel = (areaId: string) => {
    return areasById?.[areaId]?.name ?? "";
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Grid container direction="column" spacing={2}>
      <Grid item>
        {fields.map((field, index) => (
          <AllocationField
            key={field.id}
            field={field}
            index={index}
            label={getAreaLabel(field.areaId)}
            remove={remove}
            fieldsLength={fields.length}
          />
        ))}
      </Grid>
      <Grid item>
        <Divider orientation="horizontal" />
      </Grid>
      <Grid item width={1} sx={{ mb: 2 }}>
        <AllocationSelect filteredAreas={filteredAreas} append={append} />
      </Grid>
    </Grid>
  );
}

export default Fields;
