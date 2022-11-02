import { Box, Button, Divider } from "@mui/material";
import * as R from "ramda";
import { Pred } from "ramda";
import { useState } from "react";
import { StudyMetadata } from "../../../../../../../../common/types";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  SubmitHandlerPlus,
  UseFormReturnPlus,
} from "../../../../../../../common/Form";
import SearchFE from "../../../../../../../common/fieldEditors/SearchFE";
import { isSearchMatching } from "../../../../../../../../utils/textUtils";
import FormDialog from "../../../../../../../common/dialogs/FormDialog";
import {
  getFieldNames,
  getThematicTrimmingFormFields,
  setThematicTrimmingConfig,
  ThematicTrimmingFormFields,
} from "./utils";
import usePromiseWithSnackbarError from "../../../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../../../common/utils/UsePromiseCond";
import BackdropLoading from "../../../../../../../common/loaders/BackdropLoading";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

function ThematicTrimmingDialog(props: Props) {
  const { study, open, onClose } = props;
  const [search, setSearch] = useState("");

  const res = usePromiseWithSnackbarError(
    () => getThematicTrimmingFormFields(study.id),
    {
      errorMessage: "Cannot get thematic trimming form fields", // TODO i18n
      deps: [study.id],
    }
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUpdateConfig =
    (api: UseFormReturnPlus<ThematicTrimmingFormFields>, fn: Pred) => () => {
      setSearch("");

      const newValues: ThematicTrimmingFormFields = R.map(fn, api.getValues());

      Object.entries(newValues).forEach(([key, val]) => {
        api.setValue(key as keyof ThematicTrimmingFormFields, val);
      });
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
    <UsePromiseCond
      response={res}
      ifPending={() => <BackdropLoading open />}
      ifResolved={(defaultValues) => (
        <FormDialog
          open={open}
          title="Thematic Trimming"
          config={{ defaultValues }}
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
                  setSearchValue={setSearch}
                  size="small"
                />
                <Box
                  sx={{
                    display: "flex",
                  }}
                >
                  <Button
                    color="secondary"
                    onClick={handleUpdateConfig(api, R.T)}
                  >
                    Enable all
                  </Button>
                  <Button
                    color="secondary"
                    onClick={handleUpdateConfig(api, R.F)}
                  >
                    Disable all
                  </Button>
                  <Divider
                    orientation="vertical"
                    flexItem
                    sx={{ margin: "0 5px" }}
                  />
                  <Button
                    color="secondary"
                    onClick={handleUpdateConfig(api, R.not)}
                  >
                    Reverse
                  </Button>
                </Box>
              </Box>
              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  overflow: "auto",
                  p: 1,
                }}
              >
                {getFieldNames(api.getValues())
                  .filter(([, label]) => isSearchMatching(search, label))
                  .map(([name, label]) => (
                    <SwitchFE
                      key={name}
                      name={name}
                      label={label}
                      control={api.control}
                      sx={{ width: 1 / 3, m: "0 0 5px" }}
                    />
                  ))}
              </Box>
            </>
          )}
        </FormDialog>
      )}
    />
  );
}

export default ThematicTrimmingDialog;
