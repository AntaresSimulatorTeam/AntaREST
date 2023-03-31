import { Box } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import { t } from "i18next";
import Fieldset from "../../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../../common/Form";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getCurrentAreaId,
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
  const areaId = useAppSelector(getCurrentAreaId);
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const areasById = useAppSelector(
    (state) => getStudySynthesis(state, studyId)?.areas
  );
  const areaName = areasById?.[areaId]?.name ?? "";

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
    <Fieldset
      legend={t("study.modelization.hydro.allocation.areaName", { areaName })}
      fullFieldWidth
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column-reverse",
          gap: 2,
        }}
      >
        <AllocationSelect filteredAreas={filteredAreas} append={append} />
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
      </Box>
    </Fieldset>
  );
}

export default Fields;
