import { Typography, IconButton, Grid } from "@mui/material";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import { t } from "i18next";
import { FieldArrayWithId, UseFieldArrayRemove } from "react-hook-form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { AllocationFormFields } from "./utils";

interface Props {
  field: FieldArrayWithId<AllocationFormFields, "allocation">;
  index: number;
  label: string;
  remove: UseFieldArrayRemove;
  fieldsLength: number;
}

function AllocationField({ field, index, label, remove, fieldsLength }: Props) {
  const { control } = useFormContextPlus<AllocationFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Grid container spacing={1} alignItems="center">
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
              message: t("form.field.minValue", [0]),
            },
          }}
        />
      </Grid>
      <Grid item xs={2} md={1}>
        <IconButton onClick={() => remove(index)} disabled={fieldsLength === 1}>
          <RemoveCircleOutlineIcon />
        </IconButton>
      </Grid>
    </Grid>
  );
}

export default AllocationField;
