import { Box, Button, Divider } from "@mui/material";
import { useTranslation } from "react-i18next";
import * as R from "ramda";
import { Pred } from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../../../common/types";
import { setThematicTrimmingConfig } from "../../../../../../../../services/api/study";
import BasicDialog from "../../../../../../../common/dialogs/BasicDialog";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import { useFormContext } from "../../../../../../../common/Form";
import { FormValues } from "../../utils";
import {
  getFieldNames,
  ThematicTrimmingConfig,
  thematicTrimmingConfigToDTO,
} from "./utils";
import SearchFE from "../../../../../../../common/fieldEditors/SearchFE";
import { isSearchMatching } from "../../../../../../../../utils/textUtils";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ThematicTrimmingDialog(props: Props) {
  const { study, open, onClose } = props;
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
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
    const newConfig: ThematicTrimmingConfig = R.map(fn, config);

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
      fullWidth
      actions={<Button onClick={onClose}>{t("button.close")}</Button>}
      contentProps={{
        sx: { pb: 0 },
      }}
      PaperProps={{ sx: { height: "100%" } }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          pb: 2,
        }}
      >
        <SearchFE
          sx={{ m: 0 }}
          value={search}
          setSearchValue={setSearch}
          size="small"
        />
        <Box
          sx={{
            display: "flex",
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
      </Box>
      <Box sx={{ display: "flex", flexWrap: "wrap" }}>
        {getFieldNames(getCurrentConfig())
          .filter(([, label]) => isSearchMatching(search, label))
          .map(([name, label]) => (
            <SwitchFE
              key={name}
              name={`thematicTrimmingConfig.${name}`}
              sx={{ width: 1 / 3, m: "0 0 5px" }}
              label={label}
              control={control}
            />
          ))}
      </Box>
    </BasicDialog>
  );
}

export default ThematicTrimmingDialog;
