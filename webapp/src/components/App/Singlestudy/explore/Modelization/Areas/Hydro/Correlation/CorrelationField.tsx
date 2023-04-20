import { Typography, Grid } from "@mui/material";
import { FieldArrayWithId } from "react-hook-form";
import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { CorrelationFormFields } from "./utils";
import { useFormContextPlus } from "../../../../../../../common/Form";

interface Props {
  field: FieldArrayWithId<CorrelationFormFields, "correlation">;
  index: number;
  label: string;
}

// TODO merge with AllocationField
function CorrelationField({ field, index, label }: Props) {
  const { control } = useFormContextPlus<CorrelationFormFields>();
  const { t } = useTranslation();

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
          name={`correlation.${index}.coefficient`}
          size="small"
          control={control}
          rules={{
            min: {
              value: -100,
              message: t("form.field.minValue", [-100]),
            },
            max: {
              value: 100,
              message: t("form.field.minValue", [100]),
            },
          }}
        />
      </Grid>
    </>
  );
}

export default CorrelationField;
