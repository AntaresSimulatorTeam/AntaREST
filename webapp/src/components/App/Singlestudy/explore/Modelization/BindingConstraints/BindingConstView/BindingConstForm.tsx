import { AxiosError } from "axios";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Tab, Typography } from "@mui/material";
import { useFieldArray } from "react-hook-form";
import DeleteIcon from "@mui/icons-material/Delete";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import { BindingConstFields, ConstraintType, dataToId } from "./utils";
import {
  AllClustersAndLinks,
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../common/types";
import { IFormGenerator } from "../../../../../../common/FormGenerator";
import AutoSubmitGeneratorForm from "../../../../../../common/FormGenerator/AutoSubmitGenerator";
import ConstraintItem, { ConstraintWithNullableOffset } from "./ConstraintTerm";
import { useFormContext } from "../../../../../../common/Form";
import {
  deleteConstraintTerm,
  updateBindingConstraint,
  updateConstraintTerm,
} from "../../../../../../../services/api/studydata";
import TextSeparator from "../../../../../../common/TextSeparator";
import {
  ConstraintHeader,
  ConstraintList,
  ConstraintTerm,
  MatrixContainer,
  StyledTab,
} from "./style";
import AddConstraintTermDialog from "./AddConstraintTermDialog";
import MatrixInput from "../../../../../../common/MatrixInput";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import useDebounce from "../../../../../../../hooks/useDebounce";
import { appendCommands } from "../../../../../../../services/api/variant";
import { CommandEnum } from "../../../../Commands/Edition/commandTypes";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import { setCurrentBindingConst } from "../../../../../../../redux/ducks/studyDataSynthesis";
import OutputFilters from "../../../common/OutputFilters";

const DEBOUNCE_DELAY = 200;

interface Props {
  study: StudyMetadata;
  bindingConst: string;
  options: AllClustersAndLinks;
}

export default function BindingConstForm(props: Props) {
  const { study, options, bindingConst } = props;
  const studyId = study.id;
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { control } = useFormContext<BindingConstFields>();
  const { fields, update, append, remove } = useFieldArray({
    control,
    name: "constraints",
  });

  const constraintsTerm = useMemo(
    () => fields.map((elm) => ({ ...elm, id: dataToId(elm.data) })),
    [fields]
  );

  const pathPrefix = `input/bindingconstraints/bindingconstraints`;

  const optionOperator = useMemo(
    () =>
      ["less", "equal", "greater", "both"].map((item) => ({
        label: t(`study.modelization.bindingConst.operator.${item}`),
        value: item.toLowerCase(),
      })),
    [t]
  );

  const typeOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t]
  );

  const [addConstraintTermDialog, setAddConstraintTermDialog] = useState(false);
  const [deleteConstraint, setDeleteConstraint] = useState(false);
  const [termToDelete, setTermToDelete] = useState<number>();
  const [tabValue, setTabValue] = useState(0);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const saveValue = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async (name: string, data: any) => {
      try {
        await updateBindingConstraint(studyId, bindingConst, {
          key: name,
          value: data,
        });
      } catch (error) {
        enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
      }
    },
    [bindingConst, enqueueErrorSnackbar, studyId, t]
  );

  const saveValueFormGenerator = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async (name: string, path: string, defaultValues: any, data: any) =>
      saveValue(name, data),
    [saveValue]
  );

  const saveContraintValue = useDebounce(
    async (
      index: number,
      prevConst: ConstraintType,
      constraint: ConstraintWithNullableOffset
    ) => {
      try {
        const tmpConst = prevConst;
        if (constraint.weight !== undefined) {
          tmpConst.weight = constraint.weight;
        }
        if (constraint.data) {
          tmpConst.data = constraint.data;
        }
        tmpConst.id = dataToId(tmpConst.data);
        if (constraint.offset !== undefined) {
          tmpConst.offset =
            constraint.offset !== null ? constraint.offset : undefined;
        }
        await updateConstraintTerm(study.id, bindingConst, {
          ...constraint,
          offset: tmpConst.offset,
        });
        update(index, tmpConst);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.error.updateConstraintTerm"),
          error as AxiosError
        );
      }
    },
    DEBOUNCE_DELAY
  );

  const deleteTerm = useCallback(
    async (index: number) => {
      try {
        const constraintId = dataToId(constraintsTerm[index].data);
        await deleteConstraintTerm(study.id, bindingConst, constraintId);
        remove(index);
      } catch (error) {
        enqueueErrorSnackbar(
          t("study.error.deleteConstraintTerm"),
          error as AxiosError
        );
      } finally {
        setTermToDelete(undefined);
      }
    },
    [bindingConst, enqueueErrorSnackbar, constraintsTerm, remove, study.id, t]
  );

  const handleConstraintDeletion = useCallback(async () => {
    try {
      await appendCommands(study.id, [
        {
          action: CommandEnum.REMOVE_BINDING_CONSTRAINT,
          args: {
            id: bindingConst,
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
      setDeleteConstraint(false);
    }
  }, [
    bindingConst,
    dispatch,
    enqueueErrorSnackbar,
    enqueueSnackbar,
    navigate,
    study.id,
    t,
  ]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
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
            <Button
              variant="text"
              color="error"
              onClick={() => setDeleteConstraint(true)}
              sx={{
                p: 0,
                m: 0,
                minWidth: 0,
                minHeight: 0,
              }}
            >
              <DeleteIcon />
            </Button>
          </Box>
        ),
        fields: [
          {
            type: "text",
            name: "name",
            path: `${pathPrefix}/name`,
            label: t("global.name"),
            disabled: true,
            required: t("form.field.required") as string,
          },
          {
            type: "text",
            name: "comments",
            path: `${pathPrefix}/comments`,
            label: t("study.modelization.bindingConst.comments"),
          },
          {
            type: "select",
            name: "time_step",
            path: `${pathPrefix}/type`,
            label: t("study.modelization.bindingConst.type"),
            options: typeOptions,
          },
          {
            type: "select",
            name: "operator",
            path: `${pathPrefix}/operator`,
            label: t("study.modelization.bindingConst.operator"),
            options: optionOperator,
          },
          {
            type: "switch",
            name: "enabled",
            path: `${pathPrefix}/enabled`,
            label: t("study.modelization.bindingConst.enabled"),
          },
        ],
      },
    ],
    [optionOperator, pathPrefix, t, typeOptions]
  );

  return (
    <>
      <AutoSubmitGeneratorForm
        jsonTemplate={jsonGenerator}
        saveField={saveValueFormGenerator}
      />
      {Number(study.version) >= 840 && (
        <OutputFilters control={control} onAutoSubmit={saveValue} />
      )}
      <Box
        width="100%"
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
      >
        <StyledTab
          value={tabValue}
          onChange={handleTabChange}
          aria-label="basic tabs example"
        >
          <Tab label={t("study.modelization.bindingConst.constraintTerm")} />
          <Tab label={t("global.matrix")} />
        </StyledTab>
        <Box
          sx={{
            display: "flex",
            width: "100%",
            height: "100%",
          }}
        >
          {tabValue === 0 ? (
            <>
              <ConstraintList>
                <ConstraintHeader>
                  <Button
                    variant="text"
                    color="primary"
                    onClick={() => setAddConstraintTermDialog(true)}
                  >
                    {t("study.modelization.bindingConst.addConstraintTerm")}
                  </Button>
                </ConstraintHeader>
                {constraintsTerm.map(
                  (constraint: ConstraintType, index: number) => {
                    return index > 0 ? (
                      <ConstraintTerm key={constraint.id}>
                        <TextSeparator
                          text="+"
                          rootStyle={{ my: 0.25 }}
                          textStyle={{ fontSize: "22px" }}
                        />
                        <ConstraintItem
                          options={options}
                          saveValue={(value) =>
                            saveContraintValue(index, constraint, value)
                          }
                          constraint={constraint}
                          deleteTerm={() => setTermToDelete(index)}
                          constraintsTerm={constraintsTerm}
                        />
                      </ConstraintTerm>
                    ) : (
                      <ConstraintItem
                        key={constraint.id}
                        options={options}
                        saveValue={(value) =>
                          saveContraintValue(index, constraint, value)
                        }
                        constraint={constraint}
                        deleteTerm={() => setTermToDelete(index)}
                        constraintsTerm={constraintsTerm}
                      />
                    );
                  }
                )}
              </ConstraintList>
              {addConstraintTermDialog && (
                <AddConstraintTermDialog
                  open={addConstraintTermDialog}
                  studyId={studyId}
                  bindingConstraint={bindingConst}
                  title={t("study.modelization.bindingConst.newBindingConst")}
                  onCancel={() => setAddConstraintTermDialog(false)}
                  append={append}
                  constraintsTerm={constraintsTerm}
                  options={options}
                />
              )}
              {termToDelete !== undefined && (
                <ConfirmationDialog
                  titleIcon={DeleteIcon}
                  onCancel={() => setTermToDelete(undefined)}
                  onConfirm={() => deleteTerm(termToDelete)}
                  alert="warning"
                  open
                >
                  {t(
                    "study.modelization.bindingConst.question.deleteConstraintTerm"
                  )}
                </ConfirmationDialog>
              )}
              {deleteConstraint && (
                <ConfirmationDialog
                  titleIcon={DeleteIcon}
                  onCancel={() => setDeleteConstraint(false)}
                  onConfirm={() => handleConstraintDeletion()}
                  alert="warning"
                  open
                >
                  {t(
                    "study.modelization.bindingConst.question.deleteBindingConstraint"
                  )}
                </ConfirmationDialog>
              )}
            </>
          ) : (
            <MatrixContainer>
              <MatrixInput
                study={study}
                title={t("global.matrix")}
                url={`input/bindingconstraints/${bindingConst}`}
                computStats={MatrixStats.NOCOL}
              />
            </MatrixContainer>
          )}
        </Box>
      </Box>
    </>
  );
}
