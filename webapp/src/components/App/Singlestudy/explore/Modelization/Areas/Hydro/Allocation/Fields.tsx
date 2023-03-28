import { Box } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import { useOutletContext } from "react-router";
import { useCallback, useMemo } from "react";
import { AxiosError } from "axios";
import { t } from "i18next";
import { useSnackbar } from "notistack";
import Fieldset from "../../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../../common/Form";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getCurrentAreaId,
  getStudySynthesis,
} from "../../../../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../../../../common/types";
import { AllocationFormFields, setAllocationFormFields } from "./utils";
import AllocationSelect from "./AllocationSelect";
import AllocationField from "./AllocationField";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";

export default function Fields() {
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const areaId = useAppSelector(getCurrentAreaId);
  const areas = useAppSelector((state) => getAreas(state, studyId));
  const areasById = useAppSelector(
    (state) => getStudySynthesis(state, studyId)?.areas
  );
  const { control, setValue } = useFormContextPlus<AllocationFormFields>();
  const { fields, append } = useFieldArray({
    control,
    name: "allocation",
  });

  // Get a list of all the area IDs that are allocated
  const allocatedAreaIds = useMemo(
    () => fields.map((field) => field.areaId),
    [fields]
  );

  // Filter the list of areas to only include those that are not allocated
  const filteredAreas = useMemo(
    () => areas.filter((area) => !allocatedAreaIds.includes(area.id)),
    [areas, allocatedAreaIds]
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  // Get the name of an area based on its ID.
  const getAreaLabel = useCallback(
    (areaId: string) => {
      return areasById?.[areaId]?.name ?? "";
    },
    [areasById]
  );

  // Append a new allocation field to the form values.
  const appendField = useCallback(
    (obj: { areaId: string; coefficient: number }) => {
      append(obj);
    },
    [append]
  );

  // Remove an allocation field at the specified index from the form values and the server.
  const removeField = useCallback(
    async (index: number) => {
      // Make sure that the current area is not deleted.
      const currentArea = areas.find((area) => area.id === areaId);
      const deletedAreaId = fields[index].areaId;

      if (currentArea?.id === deletedAreaId) {
        enqueueSnackbar(
          t(
            "study.modelization.hydro.allocation.error.field.delete.currentArea"
          ),
          {
            variant: "warning",
            autoHideDuration: 1800,
          }
        );
        return;
      }

      const updatedFields = fields
        .filter((_, currentIndex) => currentIndex !== index)
        .map(({ id, ...fields }) => fields);

      try {
        // TODO: implement and use deleteAllocationFormFields once it's supported by the API.
        await setAllocationFormFields(studyId, areaId, {
          allocation: updatedFields,
        });
        setValue("allocation", updatedFields);
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.modelization.hydro.allocation.error.field.delete"),
          e as AxiosError
        );
      }
    },
    [
      areaId,
      areas,
      enqueueErrorSnackbar,
      enqueueSnackbar,
      fields,
      setValue,
      studyId,
    ]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Fieldset
      legend={t("study.modelization.hydro.allocation.areaId", { areaId })}
      fullFieldWidth
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column-reverse",
          gap: 2,
        }}
      >
        <AllocationSelect
          filteredAreas={filteredAreas}
          appendField={appendField}
        />
        <Box>
          {fields.map((field, index) => (
            <AllocationField
              key={field.id}
              field={field}
              index={index}
              removeField={removeField}
              getAreaLabel={getAreaLabel}
            />
          ))}
        </Box>
      </Box>
    </Fieldset>
  );
}
