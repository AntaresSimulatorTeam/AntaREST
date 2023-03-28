import { Paper, Typography, IconButton } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { memo } from "react";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { AllocationFormFields } from "./utils";

interface Props {
  field: {
    id: string;
    areaId: string;
    coefficient: number;
  };
  index: number;
  removeField: (index: number) => void;
  getAreaLabel: (areaId: string) => string | undefined;
}

export default memo(function AllocationField({
  field,
  index,
  removeField,
  getAreaLabel,
}: Props) {
  const { control } = useFormContextPlus<AllocationFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Paper
      key={field.id}
      sx={{
        display: "flex",
        alignContent: "center",
        alignItems: "center",
        px: 2,
        borderRadius: 0,
        backgroundImage:
          "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
      }}
    >
      <Typography
        sx={{
          flex: 1,
        }}
      >
        {getAreaLabel(field.areaId)}
      </Typography>
      <NumberFE
        key={field.id}
        name={`allocation.${index}.coefficient`}
        control={control}
        size="small"
        sx={{ maxWidth: 80 }}
        rules={{
          validate: {
            required: (value) => {
              if (value < 0) {
                return false;
              }
            },
          },
        }}
      />
      <IconButton onClick={() => removeField(index)}>
        <DeleteIcon />
      </IconButton>
    </Paper>
  );
});
