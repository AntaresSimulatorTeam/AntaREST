import { Box, Button, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { Pred } from "ramda";
import { StudyMetadata } from "../../../../../../../../common/types";
import { setThematicTrimmingConfig } from "../../../../../../../../services/api/study";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import { useFormContext } from "../../../../../../../common/Form";
import { FormValues } from "../../utils";
import {
  getColumns,
  getFieldNames,
  ThematicTrimmingConfig,
  thematicTrimmingConfigToDTO,
} from "./utils";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ThematicTrimmingDialog(props: Props) {
  const { study, open, onClose } = props;
  const { t } = useTranslation();
  const { control, register, getValues, setValue } =
    useFormContext<FormValues>();

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getCurrentConfig = () => {
    return getValues("thematicTrimmingConfig");
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateConfig = (fn: Pred) => () => {
    const config = getCurrentConfig();
    const fieldNames = getFieldNames(study.version);
    const newConfig: ThematicTrimmingConfig = {
      ...getCurrentConfig(),
      ...R.map(fn, R.pick(fieldNames, config)),
    };

    // More performant than `setValue('thematicTrimmingConfig', newConfig);`
    Object.entries(newConfig).forEach(([key, value]) => {
      setValue(
        `thematicTrimmingConfig.${key as keyof ThematicTrimmingConfig}`,
        value
      );
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  register("thematicTrimmingConfig", {
    onAutoSubmit: () => {
      const config = getCurrentConfig();
      const configDTO = thematicTrimmingConfigToDTO(config);
      return setThematicTrimmingConfig(study.id, configDTO);
    },
  });

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title="Thematic Trimming"
      maxWidth="md"
      actions={<Button onClick={onClose}>{t("button.close")}</Button>}
      contentProps={{
        sx: { pb: 0 },
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          pb: 2,
        }}
      >
        <Button color="secondary" onClick={handleUpdateConfig(R.T)}>
          Enable all
        </Button>
        <Button color="secondary" onClick={handleUpdateConfig(R.F)}>
          Disable all
        </Button>
        <Divider orientation="vertical" flexItem sx={{ margin: "0 5px" }} />
        <Button color="secondary" onClick={handleUpdateConfig(R.not)}>
          Reverse
        </Button>
      </Box>
      <Box sx={{ display: "flex", justifyContent: "space-between" }}>
        {getColumns(study.version).map((column, index) => (
          <Box
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            sx={{
              display: "flex",
              flexDirection: "column",
              "& + .MuiBox-root": {
                ml: 5,
              },
            }}
          >
            {column.map(([label, name]) => (
              <SwitchFE
                key={name}
                name={`thematicTrimmingConfig.${name}`}
                sx={{
                  "& + .SwitchFE": {
                    mt: 2,
                  },
                }}
                label={label}
                control={control}
              />
            ))}
          </Box>
        ))}
      </Box>
    </BasicDialog>
  );
}

export default ThematicTrimmingDialog;
