import { Box, Button, Divider, Unstable_Grid2 as Grid } from "@mui/material";
import * as R from "ramda";
import { Pred } from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../../../common/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  SubmitHandlerPlus,
  UseFormReturnPlus,
} from "../../../../../../../common/Form/types";
import SearchFE from "../../../../../../../common/fieldEditors/SearchFE";
import { isSearchMatching } from "../../../../../../../../utils/textUtils";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import {
  getFieldNames,
  getThematicTrimmingFormFields,
  setThematicTrimmingConfig,
  ThematicTrimmingFormFields,
} from "./utils";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ThematicTrimmingDialog(props: Props) {
  const { study, open, onClose } = props;
  const [search, setSearch] = useState("");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateConfig =
    (api: UseFormReturnPlus<ThematicTrimmingFormFields>, fn: Pred) => () => {
      setSearch("");

      R.forEach(([key, val]) => {
        api.setValue(key, fn(val));
      }, R.toPairs(api.getValues()));
    };

  const handleSubmit = (
    data: SubmitHandlerPlus<ThematicTrimmingFormFields>
  ) => {
    setThematicTrimmingConfig(study.id, data.values);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      key={study.id}
      open={open}
      title="Thematic Trimming"
      config={{
        asyncDefaultValues: () => getThematicTrimmingFormFields(study.id),
      }}
      autoSubmit
      onSubmit={handleSubmit}
      onCancel={onClose}
      PaperProps={{
        // TODO: add `maxHeight` and `fullHeight` in BasicDialog`
        sx: { height: "calc(100% - 64px)", maxHeight: "900px" },
      }}
      sx={{
        ".Form": {
          display: "flex",
          flexDirection: "column",
          overflow: "auto",
        },
      }}
      maxWidth="md"
      fullWidth
    >
      {(api) => (
        <>
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
              onSearchValueChange={setSearch}
              size="small"
            />
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button color="secondary" onClick={handleUpdateConfig(api, R.T)}>
                Enable all
              </Button>
              <Button color="secondary" onClick={handleUpdateConfig(api, R.F)}>
                Disable all
              </Button>
              <Divider orientation="vertical" flexItem />
              <Button
                color="secondary"
                onClick={handleUpdateConfig(api, R.not)}
              >
                Reverse
              </Button>
            </Box>
          </Box>
          <Grid
            container
            disableEqualOverflow
            spacing={1}
            sx={{ overflow: "auto", p: 1 }}
          >
            {getFieldNames(api.getValues())
              .filter(([, label]) => isSearchMatching(search, label))
              .map(([name, label]) => (
                <Grid key={name} xs={4}>
                  <SwitchFE name={name} label={label} control={api.control} />
                </Grid>
              ))}
          </Grid>
        </>
      )}
    </FormDialog>
  );
}

export default ThematicTrimmingDialog;
