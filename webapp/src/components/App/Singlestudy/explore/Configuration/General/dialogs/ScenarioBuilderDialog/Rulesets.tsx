import { InputLabel, IconButton, Box, Button } from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";
import { useContext, useState } from "react";
import * as RA from "ramda-adjunct";
import { LoadingButton } from "@mui/lab";
import FileCopyIcon from "@mui/icons-material/FileCopy";
import AddIcon from "@mui/icons-material/Add";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import ConfigContext from "./ConfigContext";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import Form from "../../../../../../../common/Form";
import { SubmitHandlerPlus } from "../../../../../../../common/Form/types";
import { updateScenarioBuilderConfig } from "./utils";
import ConfirmationDialog from "../../../../../../../common/dialogs/ConfirmationDialog";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";

type SubmitHandlerType = SubmitHandlerPlus<{ name: string }>;

function Rulesets() {
  const {
    config,
    setConfig,
    reloadConfig,
    activeRuleset,
    setActiveRuleset,
    studyId,
  } = useContext(ConfigContext);
  const { t } = useTranslation();
  const [openForm, setOpenForm] = useState<"add" | "rename" | "">("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const allowDelete = activeRuleset && Object.keys(config).length > 1;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleRename = ({ values: { name } }: SubmitHandlerType) => {
    setOpenForm("");
    setConfig(
      (prev) => RA.renameKeys({ [activeRuleset]: name }, prev) as typeof prev,
    );
    setActiveRuleset(name);

    return updateScenarioBuilderConfig(studyId, {
      [activeRuleset]: "",
      [name]: activeRuleset,
    }).catch((err) => {
      reloadConfig();

      throw new Error(
        t(
          "study.configuration.general.mcScenarioBuilder.error.ruleset.rename",
          { 0: activeRuleset },
        ),
        { cause: err },
      );
    });
  };

  const handleAdd = ({ values: { name } }: SubmitHandlerType) => {
    setOpenForm("");
    setConfig((prev) => ({ [name]: {}, ...prev }));
    setActiveRuleset(name);

    return updateScenarioBuilderConfig(studyId, {
      [name]: {},
    }).catch((err) => {
      reloadConfig();

      throw new Error(
        t("study.configuration.general.mcScenarioBuilder.error.ruleset.add", {
          0: name,
        }),
        { cause: err },
      );
    });
  };

  const handleDelete = () => {
    const { [activeRuleset]: ignore, ...newConfig } = config;
    setConfig(newConfig);
    setActiveRuleset(Object.keys(newConfig)[0] || "");
    setConfirmDelete(false);

    updateScenarioBuilderConfig(studyId, {
      [activeRuleset]: "",
    }).catch((err) => {
      reloadConfig();

      enqueueErrorSnackbar(
        t(
          "study.configuration.general.mcScenarioBuilder.error.ruleset.delete",
          { 0: activeRuleset },
        ),
        err,
      );
    });
  };

  const handleDuplicate = () => {
    const newRulesetName = `${activeRuleset} Copy`;
    setConfig((prev) => ({ [newRulesetName]: prev[activeRuleset], ...prev }));
    setActiveRuleset(newRulesetName);

    updateScenarioBuilderConfig(studyId, {
      [newRulesetName]: activeRuleset,
    }).catch((err) => {
      reloadConfig();

      enqueueErrorSnackbar(
        t(
          "study.configuration.general.mcScenarioBuilder.error.ruleset.duplicate",
          { 0: activeRuleset },
        ),
        err,
      );
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
      >
        <InputLabel>
          {t("study.configuration.general.mcScenarioBuilder.activeRuleset")}
        </InputLabel>
        {openForm ? (
          <Form
            onSubmit={openForm === "rename" ? handleRename : handleAdd}
            hideSubmitButton
            config={{
              defaultValues: {
                name: openForm === "rename" ? activeRuleset : "",
              },
            }}
            sx={{ display: "flex", p: 0 }}
          >
            {({ control, formState: { isDirty, isSubmitting } }) => (
              <>
                <StringFE
                  name="name"
                  size="small"
                  control={control}
                  autoFocus
                  rules={{
                    required: true,
                    validate: (v) => {
                      return !Object.keys(config).find(
                        (ruleset) =>
                          v === ruleset &&
                          (openForm === "add" || v !== activeRuleset),
                      );
                    },
                  }}
                />
                <LoadingButton
                  type="submit"
                  loading={isSubmitting}
                  disabled={!isDirty}
                >
                  {t(`button.${openForm}`)}
                </LoadingButton>
                <Button onClick={() => setOpenForm("")} disabled={isSubmitting}>
                  {t("button.cancel")}
                </Button>
              </>
            )}
          </Form>
        ) : (
          <>
            <SelectFE
              value={activeRuleset}
              options={Object.keys(config)}
              size="small"
              variant="outlined"
              startCaseLabel={false}
              onChange={(event) => {
                setActiveRuleset(event.target.value as string);
              }}
            />
            <IconButton onClick={() => setOpenForm("add")}>
              <AddIcon />
            </IconButton>
            <IconButton
              onClick={() => setOpenForm("rename")}
              disabled={!activeRuleset}
            >
              <EditIcon />
            </IconButton>
            <IconButton onClick={handleDuplicate} disabled={!activeRuleset}>
              <FileCopyIcon />
            </IconButton>
            <IconButton
              onClick={() => setConfirmDelete(true)}
              disabled={!allowDelete}
            >
              <DeleteIcon />
            </IconButton>
          </>
        )}
      </Box>
      {confirmDelete && (
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
          alert="warning"
        >
          {t(
            "study.configuration.general.mcScenarioBuilder.dialog.delete.text",
            { 0: activeRuleset },
          )}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default Rulesets;
