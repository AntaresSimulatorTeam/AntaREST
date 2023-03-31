import { Box, Divider, Paper } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import Fieldset from "../../../../../../../common/Fieldset";
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
    <Fieldset>
      <Box sx={{ width: 1, height: 1 }}>
        <Paper
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            p: 2,
            backgroundImage:
              "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
          }}
        >
          <Box>
            {fields.map((field, index) => (
              <AllocationField
                key={field.id}
                field={field}
                index={index}
                label={getAreaLabel(field.areaId)}
                remove={remove}
              />
            ))}
          </Box>
          <Divider
            orientation="horizontal"
            flexItem
            sx={{ width: "95%", alignSelf: "center" }}
          />
          <AllocationSelect filteredAreas={filteredAreas} append={append} />
        </Paper>
      </Box>
    </Fieldset>
  );
}

export default Fields;
