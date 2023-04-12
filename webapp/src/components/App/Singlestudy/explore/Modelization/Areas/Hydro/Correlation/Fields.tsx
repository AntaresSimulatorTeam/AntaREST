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
import { CorrelationFormFields } from "./utils";
import CorrelationField from "./CorrelationField";
import CorrelationSelect from "./CorrelationSelect";

function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const { control } = useFormContextPlus<CorrelationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "correlation",
  });
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const areasById = useAppSelector(
    (state) => getStudySynthesis(state, studyId)?.areas
  );

  const filteredAreas = useMemo(() => {
    const correlatedAreaIds = fields.map((field) => field.areaId);
    return areas.filter((area) => !correlatedAreaIds.includes(area.id));
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
          <CorrelationField
            key={field.id}
            field={field}
            index={index}
            label={getAreaLabel(field.areaId)}
            remove={remove}
          />
        ))}
      </Grid>
      <Grid item>
        <Divider orientation="horizontal" />
      </Grid>
      <Grid item width={1} sx={{ mb: 2 }}>
        <CorrelationSelect filteredAreas={filteredAreas} append={append} />
      </Grid>
    </Grid>
  );
}

export default Fields;
