import { AxiosError } from "axios";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Tab, Typography } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { useFieldArray } from "react-hook-form";
import DeleteIcon from "@mui/icons-material/Delete";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  ACTIVE_WINDOWS_DOC_PATH,
  BC_PATH,
  BindingConstFields,
  type ConstraintTerm,
  OPERATORS,
  dataToId,
  TIME_STEPS,
} from "./utils";
import {
  AllClustersAndLinks,
  StudyMetadata,
} from "../../../../../../../common/types";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import ConstraintTermItem, {
  ConstraintWithNullableOffset,
} from "./ConstraintTerm";
import { useFormContextPlus } from "../../../../../../common/Form";
import {
  deleteConstraintTerm,
  updateBindingConstraint,
  updateConstraintTerm,
} from "../../../../../../../services/api/studydata";
import TextSeparator from "../../../../../../common/TextSeparator";
import { MatrixContainer, StyledTab, TermsHeader, TermsList } from "./style";
import AddConstraintTermDialog from "./AddConstraintTermDialog";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import useDebounce from "../../../../../../../hooks/useDebounce";
import { appendCommands } from "../../../../../../../services/api/variant";
import { CommandEnum } from "../../../../Commands/Edition/commandTypes";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../../redux/ducks/studySyntheses";
import OutputFilters from "../../../common/OutputFilters";
import DocLink from "../../../../../../common/DocLink";
import Matrix from "./Matrix";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  options: AllClustersAndLinks;
}

function BindingConstForm({ study, options, constraintId }: Props) {
  const { version: studyVersion, id: studyId } = study;
  const [t] = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const [tabValue, setTabValue] = useState(0);
  const [termToDelete, setTermToDelete] = useState<number>();
  const [constraintToDelete, setConstraintToDelete] = useState(false);
  const [openConstraintTermDialog, setOpenConstraintTermDialog] =
    useState(false);

  const { control, getValues } = useFormContextPlus<BindingConstFields>();

  const { fields, update, append, remove } = useFieldArray({
    control,
    name: "constraints",
  });

  const constraintTerms = useMemo(
    () => fields.map((term) => ({ ...term, id: dataToId(term.data) })),
    [fields],
  );

  const operatorOptions = useMemo(
    () =>
      OPERATORS.map((operator) => ({
        label: t(`study.modelization.bindingConst.operator.${operator}`),
        value: operator,
      })),
    [t],
  );

  const currentOperator = getValues("operator");
  const currentTimeStep = getValues("time_step");

  const typeOptions = useMemo(
    () =>
      TIME_STEPS.map((timeStep) => ({
        label: t(`global.time.${timeStep}`),
        value: timeStep,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSaveValue = async (filter: string, data: unknown) => {
    try {
      await updateBindingConstraint(studyId, constraintId, {
        key: filter,
        value: data,
      });
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const handleSaveFormValue = async (
    name: string,
    _path: string,
    _defaultValues: unknown,
    data: unknown,
  ) => handleSaveValue(name, data);

  const handleUpdateTerm = useDebounce(
    async (
      index: number,
      prevTerm: ConstraintTerm,
      newTerm: ConstraintWithNullableOffset,
    ) => {
      try {
        const updatedTerm = {
          ...prevTerm,
          weight: newTerm.weight || prevTerm.weight,
          data: newTerm.data || prevTerm.data,
          offset: newTerm.offset || prevTerm.offset,
        };

        updatedTerm.id = dataToId(updatedTerm.data);

        await updateConstraintTerm(study.id, constraintId, {
          ...newTerm,
          offset: updatedTerm.offset,
        });

        update(index, updatedTerm);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.error.updateConstraintTerm"),
          error as AxiosError,
        );
      }
    },
    500,
  );

  const handleDeleteTerm = async (termToDelete: number) => {
    try {
      const termId = dataToId(constraintTerms[termToDelete].data);
      await deleteConstraintTerm(study.id, constraintId, termId);
      remove(termToDelete);
    } catch (error) {
      enqueueErrorSnackbar(
        t("study.error.deleteConstraintTerm"),
        error as AxiosError,
      );
    } finally {
      setTermToDelete(undefined);
    }
  };

  const handleDeleteConstraint = async () => {
    try {
      await appendCommands(study.id, [
        {
          action: CommandEnum.REMOVE_BINDING_CONSTRAINT,
          args: {
            id: constraintId,
          },
        },
      ]);

      enqueueSnackbar(t("study.success.deleteConstraint"), {
        variant: "success",
      });

      dispatch(setCurrentBindingConst(""));

      navigate(`/studies/${study.id}/explore/modelization/bindingcontraint`);
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.deleteConstraint"), e as AxiosError);
    } finally {
      setConstraintToDelete(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const jsonGenerator: IFormGenerator<BindingConstFields> = useMemo(
    () => [
      {
        legend: (
          <Box
            sx={{
              width: "100%",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Typography
              variant="h5"
              sx={{ fontSize: "1.25rem", fontWeight: 400, lineHeight: 1.334 }}
            >
              {t("global.general")}
            </Typography>

            <Box sx={{ display: "flex" }}>
              <Button
                startIcon={<DeleteIcon />}
                color="error"
                onClick={() => setConstraintToDelete(true)}
              >
                {t("global.delete")}
              </Button>
              <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#binding-constraints`} />
            </Box>
          </Box>
        ),
        fields: [
          {
            type: "text",
            name: "name",
            path: `${BC_PATH}/name`,
            label: t("global.name"),
            disabled: true,
            required: t("form.field.required"),
            sx: { maxWidth: 200 },
          },
          {
            type: "text",
            name: "test", // TODO group
            path: `${BC_PATH}/group`,
            label: t("global.group"),
            sx: { maxWidth: 200 },
          },
          {
            type: "text",
            name: "comments",
            path: `${BC_PATH}/comments`,
            label: t("study.modelization.bindingConst.comments"),
            sx: { maxWidth: 200 },
          },
          {
            type: "select",
            name: "time_step",
            path: `${BC_PATH}/type`,
            label: t("study.modelization.bindingConst.type"),
            options: typeOptions,
            sx: { maxWidth: 120 },
          },
          {
            type: "select",
            name: "operator",
            path: `${BC_PATH}/operator`,
            label: t("study.modelization.bindingConst.operator"),
            options: operatorOptions,
            sx: { maxWidth: 120 },
          },
          {
            type: "switch",
            name: "enabled",
            path: `${BC_PATH}/enabled`,
            label: t("study.modelization.bindingConst.enabled"),
          },
        ],
      },
    ],
    [t, operatorOptions, typeOptions],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={handleSaveFormValue}
      />

      {studyVersion >= "840" && (
        <OutputFilters control={control} onAutoSubmit={handleSaveValue} />
      )}

      <StyledTab value={tabValue} onChange={handleTabChange}>
        <Tab label={t("study.modelization.bindingConst.constraintTerm")} />
        <Tab label={t("study.modelization.bindingConst.timeSeries")} />
      </StyledTab>

      <Box
        sx={{
          display: "flex",
          width: 1,
          height: 1,
        }}
      >
        {tabValue === 0 && (
          <TermsList>
            <TermsHeader>
              <Button
                variant="contained"
                size="small"
                color="primary"
                startIcon={<AddCircleOutlineRoundedIcon />}
                onClick={() => setOpenConstraintTermDialog(true)}
              >
                {t("study.modelization.bindingConst.addConstraintTerm")}
              </Button>
            </TermsHeader>
            {constraintTerms.map((term: ConstraintTerm, index: number) => (
              <Box key={term.id}>
                {index > 0 && (
                  <TextSeparator text="+" textStyle={{ fontSize: "16px" }} />
                )}
                <ConstraintTermItem
                  options={options}
                  saveValue={(newTerm) =>
                    handleUpdateTerm(index, term, newTerm)
                  }
                  term={term}
                  deleteTerm={() => setTermToDelete(index)}
                  constraintTerms={constraintTerms}
                />
              </Box>
            ))}
          </TermsList>
        )}

        {tabValue === 1 && (
          <MatrixContainer>
            <Matrix
              study={study}
              operator={currentOperator}
              timeStep={currentTimeStep}
              constraintId={constraintId}
            />
          </MatrixContainer>
        )}
      </Box>

      {openConstraintTermDialog && (
        <AddConstraintTermDialog
          open={openConstraintTermDialog}
          studyId={studyId}
          constraintId={constraintId}
          title={t("study.modelization.bindingConst.newBindingConst")}
          onCancel={() => setOpenConstraintTermDialog(false)}
          append={append}
          constraintTerms={constraintTerms}
          options={options}
        />
      )}

      {termToDelete !== undefined && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setTermToDelete(undefined)}
          onConfirm={() => handleDeleteTerm(termToDelete)}
          alert="warning"
          open
        >
          {t("study.modelization.bindingConst.question.deleteConstraintTerm")}
        </ConfirmationDialog>
      )}

      {constraintToDelete && (
        <ConfirmationDialog
          titleIcon={DeleteIcon}
          onCancel={() => setConstraintToDelete(false)}
          onConfirm={() => handleDeleteConstraint()}
          alert="warning"
          open
        >
          {t(
            "study.modelization.bindingConst.question.deleteBindingConstraint",
          )}
        </ConfirmationDialog>
      )}
    </>
  );
}

export default BindingConstForm;
