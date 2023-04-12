import { Typography, IconButton, Grid } from "@mui/material";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
import { FieldArrayWithId, UseFieldArrayRemove } from "react-hook-form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { CorrelationFormFields } from "./utils";

interface Props {
  field: FieldArrayWithId<CorrelationFormFields, "correlation">;
  index: number;
  label: string;
  remove: UseFieldArrayRemove;
}

function CorrelationField({ field, index, label, remove }: Props) {
  const { control } = useFormContextPlus<CorrelationFormFields>();

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
          name={`correlation.${index}.coefficient`}
          control={control}
          size="small"
          rules={{
            min: {
              value: -100,
              message: "min: -100%",
            },
            max: {
              value: 100,
              message: "max: 100%",
            },
          }}
        />
      </Grid>
      <Grid item xs={2} md={1}>
        <IconButton onClick={() => remove(index)}>
          <RemoveCircleOutlineIcon />
        </IconButton>
      </Grid>
    </Grid>
  );
}

export default CorrelationField;
