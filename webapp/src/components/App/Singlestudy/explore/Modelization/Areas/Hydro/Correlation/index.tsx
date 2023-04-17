import { Box, Paper } from "@mui/material";
import { useOutletContext } from "react-router";
import { useMemo } from "react";
import { useFieldArray } from "react-hook-form";
import Form, { useFormContextPlus } from "../../../../../../../common/Form";
import { StudyMetadata } from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import {
  getAreas,
  getCurrentAreaId,
} from "../../../../../../../../redux/selectors";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import {
  CorrelationFormFields,
  getCorrelationFormFields,
  setCorrelationFormFields,
} from "./utils";
import DynamicList from "../../../../../../../common/DynamicList";
import CorrelationField from "./CorrelationField";

function Correlation() {
  const areaId = useAppSelector(getCurrentAreaId);
  const {
    study: { id: studyId },
  } = useOutletContext<{ study: StudyMetadata }>();
  const { control } = useFormContextPlus<CorrelationFormFields>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: "correlation",
  });
  const areas = useAppSelector((state) => getAreas(state, studyId));

  const filteredAreas = useMemo(() => {
    const areaIds = fields.map((field) => field.areaId);
    return areas.filter((area) => !areaIds.includes(area.id));
  }, [areas, fields]);

  const options = useMemo(
    () =>
      filteredAreas.map((area) => ({
        label: area.name,
        value: area.id,
      })),
    [filteredAreas]
  );

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = (data: SubmitHandlerPlus<CorrelationFormFields>) => {
    setCorrelationFormFields(studyId, areaId, {
      correlation: data.values.correlation,
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: 1,
        height: 1,
        p: 2,
        overflow: "auto",
      }}
    >
      <Paper
        sx={{
          backgroundImage:
            "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
        }}
      >
        <Form
          key={studyId + areaId}
          config={{
            defaultValues: () => getCorrelationFormFields(studyId, areaId),
          }}
          onSubmit={handleSubmit}
          sx={{ p: 3 }}
        >
          <DynamicList
            items={fields}
            renderItem={(item, index) => (
              <CorrelationField
                key={item.id}
                field={item}
                index={index}
                label={`${item.areaId}`}
                remove={remove}
                control={control}
              />
            )}
            options={options}
            onAdd={(value: string) =>
              append({
                areaId: value,
                coefficient: 0,
              })
            }
          />
        </Form>
      </Paper>
    </Box>
  );
}

export default Correlation;
