import { Typography, Grid } from "@mui/material";
import { t } from "i18next";
import { FieldArrayWithId } from "react-hook-form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { AllocationFormFields } from "./utils";

interface Props {
  field: FieldArrayWithId<AllocationFormFields, "allocation">;
  index: number;
  label: string;
}

function AllocationField({ field, index, label }: Props) {
  const { control } = useFormContextPlus<AllocationFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Grid item xs={4} md={2}>
        <Typography
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </Typography>
      </Grid>
      <Grid item xs={4} md={2}>
        <NumberFE
          key={field.id}
          name={`allocation.${index}.coefficient`}
          control={control}
          size="small"
          rules={{
            min: {
              value: 0,
              message: t("form.field.minValue", { 0: 0 }),
            },
          }}
        />
      </Grid>
    </>
  );
}

export default AllocationField;
