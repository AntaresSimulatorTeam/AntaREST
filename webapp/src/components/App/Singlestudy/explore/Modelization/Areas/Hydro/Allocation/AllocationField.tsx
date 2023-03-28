import { Paper, Typography, IconButton } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { AllocationFormFields } from "./utils";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";

interface Props {
  field: {
    id: string;
    areaId: string;
    coefficient: number;
  };
  index: number;
  label: string;
  remove: (index: number) => void;
}

function AllocationField({ field, index, label, remove }: Props) {
  const { control } = useFormContextPlus<AllocationFormFields>();
  const currentAreaId = useAppSelector(getCurrentAreaId);

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
        justifyContent: "strech",
        px: 2,
        borderRadius: 0,
        backgroundImage:
          "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
      }}
    >
      <Typography sx={{ flex: 1 }}>{label}</Typography>
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

      <IconButton
        onClick={() => remove(index)}
        disabled={field.areaId === currentAreaId}
        style={{
          visibility: field.areaId === currentAreaId ? "hidden" : "visible",
        }}
      >
        <DeleteIcon />
      </IconButton>
    </Paper>
  );
}

export default AllocationField;
