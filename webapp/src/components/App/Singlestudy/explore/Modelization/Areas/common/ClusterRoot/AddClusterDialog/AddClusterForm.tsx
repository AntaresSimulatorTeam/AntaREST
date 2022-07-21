import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { useFormContext } from "../../../../../../../../common/Form";
import SelectFE from "../../../../../../../../common/fieldEditors/SelectFE";
import { AddClustersFields } from "../utils";
import StringFE from "../../../../../../../../common/fieldEditors/StringFE";

interface Props {
  clusterGroupList: Array<string>;
}

function AddClusterForm(props: Props) {
  const { clusterGroupList } = props;
  const { control } = useFormContext<AddClustersFields>();
  const { t } = useTranslation();
  const groupOptions = clusterGroupList.map((item) => ({
    label: item,
    value: item,
  }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/* Name */}
      <StringFE
        name="name"
        sx={{ mx: 0, mb: 2, flex: 1 }}
        label={t("global.name")}
        variant="filled"
        control={control}
        fullWidth
        rules={{
          required: t("form.field.required") as string,
        }}
      />
      <Box
        sx={{
          display: "flex",
          width: "100%",
        }}
      >
        <SelectFE
          name="group"
          label={t(`study.modelization.clusters.group`)}
          options={groupOptions}
          control={control}
          formControlProps={{
            sx: {
              flex: 1,
              boxSizing: "border-box",
            },
          }}
          sx={{ width: "auto", minWidth: "250px" }}
          rules={{
            required: t("form.field.required") as string,
          }}
        />
      </Box>
    </>
  );
}

export default AddClusterForm;
