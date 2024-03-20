import { AxiosError } from "axios";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Tab } from "@mui/material";
import AddCircleOutlineRoundedIcon from "@mui/icons-material/AddCircleOutlineRounded";
import { useFieldArray } from "react-hook-form";
import DeleteIcon from "@mui/icons-material/Delete";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  type ConstraintTerm,
  generateTermId,
  BindingConstraint,
} from "./utils";
import {
  AllClustersAndLinks,
  StudyMetadata,
} from "../../../../../../../common/types";
import ConstraintTermItem, {
  ConstraintWithNullableOffset,
} from "./ConstraintTerm";
import { useFormContextPlus } from "../../../../../../common/Form";
import {
  deleteConstraintTerm,
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
import Matrix from "./Matrix";

interface Props {
  study: StudyMetadata;
  constraintId: string;
  options: AllClustersAndLinks;
}

// TODO rename ConstraintTermsFields
function BindingConstForm({ study, options, constraintId }: Props) {
  const { id: studyId } = study;
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

  const { control, getValues } = useFormContextPlus<BindingConstraint>();

  const { fields, update, append, remove } = useFieldArray({
    control,
    name: "constraints",
  });

  const constraintTerms = useMemo(
    () => fields.map((term) => ({ ...term, id: generateTermId(term.data) })),
    [fields],
  );

  const currentOperator = getValues("operator");

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

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

        updatedTerm.id = generateTermId(updatedTerm.data);

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
      const termId = generateTermId(constraintTerms[termToDelete].data);
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
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/*   <Box
        sx={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box sx={{ display: "flex" }}>
          <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#binding-constraints`} />

          <Button
            startIcon={<DeleteIcon />}
            color="error"
            onClick={() => setConstraintToDelete(true)}
          >
            {t("global.delete")}
          </Button>
        </Box>
      </Box> */}
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
