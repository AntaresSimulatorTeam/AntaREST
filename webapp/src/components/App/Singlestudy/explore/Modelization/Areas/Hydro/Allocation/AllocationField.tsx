import { Typography, IconButton, Box } from "@mui/material";
import RemoveCircleOutlineIcon from "@mui/icons-material/RemoveCircleOutline";
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
    <Box
      key={field.id}
      sx={{
        display: "flex",
        alignContent: "center",
        alignItems: "center",
      }}
    >
      <Typography
        sx={{
          width: "20%",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </Typography>
      <NumberFE
        key={field.id}
        name={`allocation.${index}.coefficient`}
        control={control}
        size="small"
        sx={{ maxWidth: 150 }}
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
        <RemoveCircleOutlineIcon />
      </IconButton>
    </Box>
  );
}

export default AllocationField;
